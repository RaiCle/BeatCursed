#### Imports ####
import os
os.environ['SDL_VIDEO_CENTERED'] = '1'
from pygame import Rect
from pgzero.actor import Actor
import pgzrun
import random

#### Bases ####
# Tamanho da janela
WIDTH = 800
HEIGHT = 600

# Estado do jogo: 'menu', 'controle', 'jogo'
game_state = 'menu'
jogo_ativo = True
icon = Actor("logo", (400, 120))
pontuacao = 0
recorde = 0

# Volume e som
volume = 1.0
muted = False

# Botoes do menu
start = Actor("btn_play", (400, 250))
controls = Actor("btn_opt", (400, 330))
quit = Actor("btn_exit", (400, 410))
back_button = Actor("btn_back", (50, 25))
volume_bar = Rect(585, 25, 150, 20)
menu_buttons = {
    'start': start,
    'controls': controls,
    'quit': quit
}

# Icones de som
icon_on = Actor("som_on", (765, 35))
icon_off = Actor("som_off", (765, 35))

#Fundo em game
background = Actor("background")
gameover_tela = Actor("tela_gameover")

# fundo option
menu_control = Actor("menu_control", (400, 330))

#### Regras especificas ####
# Indicadores ritmicos
indicador_ritmico = [Actor(f"indicador_ritmico_{i}") for i in range(3)]
estado_ritmo = 0  # 0: neutro, 1: direita, 2: esquerda
estado_ritmo_timer = 0
notas_ritmicas = []  # lista de dicts: {x, y, tipo, ativa}
velocidade_nota = 2  # você pode ajustar manualmente aqui
indicador_x = 400  # centro da tela para referência
seta_ataque = Actor("nota_ataque")
seta_defesa = Actor("nota_defesa")
ultimos_tipos = []  # guarda os últimos tipos gerados: 'ataque' ou 'defesa'

contador_notas = 0
batida = 60  # a cada 60 frames gera uma nota

# Lista de zonas
zonas = []
ZONA_LARGURA = 160
ZONA_Y = 500

# Status do heroi
hero_vida = 100
hero_defesa = 5
hero_dano = 10
hero_action_timer = 0
hero_action_duration = 20
em_combate = False
hero_frame = 0
hero_timer = 0
hero_speed = 6
hero_index = 0
hero_action = "idle"
hero_pos_x = ZONA_LARGURA // 2

# Inimigo
inimigos = {} 

# Pisos
piso = [Actor(f"piso_{i}") for i in range(5)]

# Bau
chest_frame = 0
chest_timer = 0
chest_speed = 6  # quanto menor, mais rápido
estado_bau = False  

# Variaveis para o bau
opcoes_bau = []  # strings: "cura", "escudo", "dano"
selecionado_bau = 0  # 0 ou 1
menu_bau = Actor("menu_bau", (400, 300))
btn_curar = Actor("btn_curar")
btn_escudo = Actor("btn_escudo")
btn_dano = Actor("btn_dano")

# Input cooldown
input_cooldown = 0
input_cooldown_max = 30

#### Frames ####
# Frames de animacao do heroi
hero_idle_frames = [Actor(f"hero_idle_{i}") for i in range(5)]
hero_walk_frames = [Actor(f"hero_walk_{i}") for i in range(4)]
hero_defend_frames = [Actor(f"hero_defend_{i}") for i in range(3)]
hero_attack_frames = [Actor(f"hero_attack_{i}") for i in range(5)]

# Frames de animacao do inimigo
enemy_idle_frames = [Actor(f"enemy_idle_{i}") for i in range(6)]
enemy_hit_frames = [Actor(f"enemy_hit_{i}") for i in range(5)]
enemy_die_frames = [Actor(f"enemy_die_{i}") for i in range(10)]
enemy_attack_frames = [Actor(f"enemy_atack_{i}") for i in range(8)]

# Frames de animacao do bau
chest_idle_frames = [Actor(f"chest_idle_{i}") for i in range(6)]


#### Draws do jogo ###
def draw():
    screen.clear()
    if game_state == 'menu':
        draw_menu()
    elif game_state == 'controle':
        draw_controls()
    elif game_state == 'jogo':
        draw_jogo()
    elif game_state == 'gameover':
        draw_game_over()

def draw_game_over():
    screen.clear()
    gameover_tela.topleft = (0, 0)
    gameover_tela.draw()
    screen.draw.text(f"Sua pontuacao: {pontuacao}", center=(WIDTH//2, HEIGHT//2 + 50), fontsize=36, color="white")
    screen.draw.text(f"Recorde: {recorde}", center=(WIDTH//2, HEIGHT//2 + 80), fontsize=28, color="gold")
    screen.draw.text("Pressione qualquer tecla ou clique para voltar ao menu", center=(WIDTH//2, HEIGHT - 40), fontsize=20, color="gray")

def draw_menu():
    background.topleft = (0, 0)
    background.draw()
    icon.draw()

    start.draw()
    controls.draw()
    quit.draw()

    draw_volume_controls()

def draw_controls():
    background.topleft = (0, 0)
    background.draw()
    menu_control.draw()
    back_button.draw()
    draw_volume_controls()

def draw_jogo():
    background.topleft = (0, 0)
    background.draw()

    # Pontuação no canto superior direito
    screen.draw.text(f"Pontos: {pontuacao}", topright=(780, 10), fontsize=28, color="white")
    screen.draw.text(f"Recorde: {recorde}", topright=(780, 40), fontsize=20, color="gold")

    ZONAS = [i * ZONA_LARGURA + ZONA_LARGURA // 2 for i in range(5)]
    for i, tipo in enumerate(zonas):
        x = ZONAS[i]
        piso[i].pos = (x, 575)
        piso[i].draw()
        if tipo == "inimigo":
            if i in inimigos:
                draw_enemy(inimigos[i])
                if inimigos[i]['estado'] != 'dead':
                    vida = inimigos[i].get('vida', 0)
                    screen.draw.text(f"{vida} HP", center=(x, ZONA_Y), fontsize=20, color="red")
            else:
                # Zona marcada como 'inimigo', mas não existe inimigo criado ainda.
                pass
        elif tipo == "bau":
            chest_idle_frames[chest_frame].pos = (x, ZONA_Y + 30)
            chest_idle_frames[chest_frame].draw()

    # Desenha indicador rítmico
    indicador_ritmico[estado_ritmo].pos = (indicador_x, 80)
    indicador_ritmico[estado_ritmo].draw()

    # Desenha notas 
    for nota in notas_ritmicas:
        if nota['ativa'] and nota['atraso'] <= 0:
            img = seta_ataque if nota['tipo'] == 'ataque' else seta_defesa
            img.pos = (nota['x'], nota['y']+32)
            img.draw()

    draw_hero()

    if estado_bau:
        menu_bau.draw()

        for i, opcao in enumerate(opcoes_bau):
            x = 400
            y = 270 if i == 0 else 370  

            if opcao == "cura":
                btn_curar.pos = (x, y)
                btn_curar.draw()
            elif opcao == "escudo":
                btn_escudo.pos = (x, y)
                btn_escudo.draw()
            elif opcao == "dano":
                btn_dano.pos = (x, y)
                btn_dano.draw()

            direcao = "pressione Esquerda" if i == 0 else "pressione Direita"
            screen.draw.text(direcao, center=(x, y + 45), fontsize=20, color="white")

def draw_volume_controls():
    if muted:
        icon_off.draw()
    else:
        icon_on.draw()
    screen.draw.filled_rect(volume_bar, "gray")
    fill = int(volume_bar.width * (0 if muted else volume))
    screen.draw.filled_rect(Rect(volume_bar.left, volume_bar.top, fill, volume_bar.height), "lightgreen")
    screen.draw.rect(volume_bar, "white")

def draw_hero():
    y = ZONA_Y + 35
    frame = 0
    screen.draw.text(f"{hero_vida} HP", center=(hero_pos_x, ZONA_Y - 10), fontsize=20, color="green")
    screen.draw.text(f"{hero_defesa} DEF", center=(hero_pos_x, ZONA_Y + 5), fontsize=16, color="blue")

    if hero_action == "idle":
        frame = hero_frame % len(hero_idle_frames)
        hero_idle_frames[frame].pos = (hero_pos_x, y)
        hero_idle_frames[frame].draw()

    elif hero_action == "walk":
        frame = hero_frame % len(hero_walk_frames)
        hero_walk_frames[frame].pos = (hero_pos_x, y)
        hero_walk_frames[frame].draw()

    elif hero_action == "defend":
        frame = hero_frame % len(hero_defend_frames)
        hero_defend_frames[frame].pos = (hero_pos_x, y)
        hero_defend_frames[frame].draw()

    elif hero_action == "attack":
        frame = min(hero_frame, len(hero_attack_frames) - 1)
        hero_attack_frames[frame].pos = (hero_pos_x, y)
        hero_attack_frames[frame].draw()

def draw_enemy(inimigo):
    x, y = inimigo['pos']
    frame = inimigo['frame']

    if inimigo['estado'] == 'idle':
        enemy_idle_frames[frame].pos = (x, y)
        enemy_idle_frames[frame].draw()
    elif inimigo['estado'] == 'hit':
        if frame < len(enemy_hit_frames):
            enemy_hit_frames[frame].pos = (x, y)
            enemy_hit_frames[frame].draw()
    elif inimigo['estado'] == 'dead':
        dead_frame = min(frame, len(enemy_die_frames) - 1)
        enemy_die_frames[dead_frame].pos = (x, y)
        enemy_die_frames[dead_frame].draw()
    elif inimigo['estado'] == 'attack':
        if frame < len(enemy_attack_frames):
            enemy_attack_frames[frame].pos = (x, y)
            enemy_attack_frames[frame].draw()

#### Funcoes especificas ####
def update_hero():
    global hero_timer, hero_frame, hero_action_timer, hero_action

    hero_frame = max(0, hero_frame)
    hero_timer += 1
    if hero_timer >= hero_speed:
        hero_timer = 0
        hero_frame += 1

        # Limita o valor do frame com base na acao atual
        if hero_action == "idle":
            hero_frame %= len(hero_idle_frames)
        elif hero_action == "walk":
            hero_frame %= len(hero_walk_frames)
        elif hero_action == "defend":
            hero_frame %= len(hero_defend_frames)
        elif hero_action == "attack":
            if hero_frame >= len(hero_attack_frames):
                hero_frame = len(hero_attack_frames) - 1  

    # Reseta para idle depois da acao terminar
    if hero_action != "idle":
        hero_action_timer += 1
        if hero_action_timer >= hero_action_duration:
            hero_action = "idle"
            hero_action_timer = 0
            hero_frame = 0

def mover_heroi_suave():
    global hero_pos_x
    destino = ZONA_LARGURA * hero_index + ZONA_LARGURA // 2
    if hero_pos_x < destino:
        hero_pos_x += 5
        if hero_pos_x > destino:
            hero_pos_x = destino
    elif hero_pos_x > destino:
        hero_pos_x -= 5
        if hero_pos_x < destino:
            hero_pos_x = destino

def gerar_conteudo(prev1, prev2):
    chance = random.randint(0, 100)
    if prev1 == 'nada' and prev2 == 'nada':
        return random.choices(['inimigo', 'bau'], weights=[70, 30])[0]
    elif prev1 == 'nada':
        return 'nada' if chance <= 25 else gerar_padrao()
    else:
        return gerar_padrao()

def gerar_padrao():
    chance = random.randint(0, 100)
    if chance <= 50:
        return 'nada'
    elif chance <= 85:
        return 'inimigo'
    else:
        return 'bau'

def inicializar_inimigos():
    global inimigos
    inimigos = {}
    for i, tipo in enumerate(zonas):
        if tipo == 'inimigo':
            inimigos[i] = {
                'vida': random.randint(20, 60),
                'estado': 'idle',
                'frame': 0,
                'timer': 0,
                'atk_timer': 0,
                'ataque': False,
                'inimigo_timer_ataque': 0,
                'pos': (ZONA_LARGURA * i + ZONA_LARGURA // 2, ZONA_Y + 30)
            }

def sortear_opcoes_bau():
    global opcoes_bau, selecionado_bau
    itens = ["cura", "escudo", "dano"]
    pesos = [34, 33, 33]

    while True:
        escolha1 = random.choices(itens, pesos)[0]
        escolha2 = random.choices(itens, pesos)[0]
        if escolha1 != escolha2:
            break

    opcoes_bau = [escolha1, escolha2]
    selecionado_bau = 0

def gerar_zonas():
    nova = []
    prev1 = 'algo'
    prev2 = 'algo'
    for i in range(5):
        if i == 0:
            nova.append('heroi')
        else:
            conteudo = gerar_conteudo(prev1, prev2)
            nova.append(conteudo)
            prev2 = prev1
            prev1 = conteudo
    return nova

def spawn_nota_ritmica(tipo, atraso=0):
    nota = {
        'tipo': tipo,  # 'ataque' ou 'defesa'
        'x': 0 if tipo == 'defesa' else WIDTH,
        'y': 80,
        'ativa': True,
        'atraso': atraso,  # atraso em frames
        'verificado': False,      # se essa nota já foi processada para ataque
        'defendido': False,       # se o jogador defendeu a tempo
        'pronta_para_ataque': False,  # controlar momento do ataque inimigo
    }
    notas_ritmicas.append(nota)

def checar_zona():
    global estado_bau, pontuacao
    zona = zonas[hero_index]
    if zona == 'inimigo':
        print("Enfrentou inimigo")
    elif zona == 'bau':
        print("Encontrou um bau!")
        estado_bau = True
        pontuacao += 25
        sortear_opcoes_bau()

def iniciar_nova_fase():
    global zonas, hero_index, hero_pos_x
    zonas = gerar_zonas()
    inicializar_inimigos() 
    hero_index = 0
    hero_pos_x = ZONA_LARGURA // 2
    print("Nova fase iniciada")

def iniciar_combate(nota_valida):
    global em_combate, hero_action, pontuacao

    zona_alvo = hero_index + 1
    if zona_alvo not in inimigos:
        print("Erro: combate iniciado mas nenhum inimigo encontrado na zona", zona_alvo)
        return

    # Verifica se existe uma nota de ataque valida
    nota_valida['ativa'] = False

    inimigo = inimigos[zona_alvo]
    if inimigo['vida'] <= 0:
        pontuacao += 100
        print("Inimigo ja esta morto.")
        return

    em_combate = True
    hero_action = "attack"
    hero_frame = 0

    dano = hero_dano
    inimigo['vida'] -= dano
    inimigo['estado'] = 'hit'
    inimigo['frame'] = 0
    inimigo['timer'] = 0

    print(f"Ataque! Inimigo na zona {zona_alvo} levou {dano} de dano e agora tem {inimigo['vida']} de vida.")


    if inimigo['vida'] <= 0:
        print("Inimigo derrotado!")
        inimigo['estado'] = 'dead'
        inimigo['frame'] = 0
        inimigo['timer'] = 0
        em_combate = False
        zonas[zona_alvo] = "inimigo"
        pontuacao += 100

#### Regras de input ####
def on_mouse_down(pos):
    global game_state, muted, volume

    if game_state == 'gameover':
        game_state = 'menu'
        music.play("fundo")
        music.set_volume(volume if not muted else 0)
        return
    
    notas_ritmicas.clear()
    if game_state == 'menu':
        for name, actor in menu_buttons.items():
            if actor.collidepoint(pos):
                if name == 'start':
                    start_game()
                elif name == 'controls':
                    game_state = 'controle'
                elif name == 'quit':
                    exit()
    elif game_state == 'controle':
        if back_button.collidepoint(pos):
            game_state = 'menu'
    if icon_on.collidepoint(pos) or icon_off.collidepoint(pos):
        muted = not muted
        music.set_volume(0 if muted else volume)
    if volume_bar.collidepoint(pos):
        pct = (pos[0] - volume_bar.left) / volume_bar.width
        volume = max(0.0, min(1.0, pct))
        if not muted:
            music.set_volume(volume)

def on_key_down(key):
    global game_state, hero_index, hero_action, input_cooldown, estado_ritmo, estado_ritmo_timer , estado_bau, hero_vida, hero_defesa, hero_dano, pontuacao

    if game_state == 'gameover':
        game_state = 'menu'
        music.play("fundo")
        music.set_volume(volume if not muted else 0)
        return

    if input_cooldown > 0:
        return
    input_cooldown = input_cooldown_max

    if estado_bau:
        if key == keys.RIGHT:
            opcao = opcoes_bau[1]  # escolheu a da direita
        elif key == keys.LEFT:
            opcao = opcoes_bau[0]  # escolheu a da esquerda
        else:
            return  # ignora outras teclas durante o baú aberto

        # Aplica efeito da opção escolhida
        if opcao == "cura":
            cura = random.randint(5, 20)
            hero_vida = min(100, hero_vida + cura)
            print(f"Curou {cura} de vida. Agora: {hero_vida}")
        elif opcao == "escudo":
            escudo = random.randint(2, 5)
            hero_defesa += escudo
            print(f"Recebeu {escudo} de escudo. Agora: {hero_defesa}")
        elif opcao == "dano":
            hero_dano += 2
            print(f"Aumentou dano base! Agora: {hero_dano}")

        estado_bau = False
        zonas[hero_index] = 'nada'
        return

    if game_state == 'controle' and key == keys.ESCAPE:
        game_state = 'menu'

    elif game_state == 'jogo':
        # DETECCAO ritimico
        if key == keys.RIGHT:
            estado_ritmo = 1
            for nota in notas_ritmicas:
                if nota['tipo'] == 'ataque' and nota['ativa']:
                    if indicador_x - 15 <= nota['x'] <= indicador_x + 45:
                        nota['ativa'] = False

                        destino = hero_index + 1
                        if (destino < len(zonas) and zonas[destino] == "inimigo" and
                            inimigos.get(destino, {}).get('vida', 0) > 0):
                            iniciar_combate(nota)
                        else:
                            print("Nenhum inimigo valido a frente para atacar.")
                        break  # so processa uma nota por vez

        elif key == keys.LEFT:
            estado_ritmo = 2
            for nota in notas_ritmicas:
                if nota['tipo'] == 'defesa' and nota['ativa']:
                    if indicador_x - 45 <= nota['x'] <= indicador_x + 15:
                        print("DEFESA CERTA!")
                        nota['defendido'] = True
                        break  # so defende uma nota por vez

        if key == keys.ESCAPE:
            game_state = 'menu'
            music.stop()
            music.play("fundo")
            music.set_volume(volume if not muted else 0)

        elif key == keys.RIGHT and hero_index < 4:
            destino = hero_index + 1
            if zonas[destino] == "inimigo" and inimigos.get(destino, {}).get('vida', 0) > 0:
                # Localiza uma nota de ataque valida (no range e ativa)
                nota_valida = None
                for n in notas_ritmicas:
                    if n['tipo'] == 'ataque' and n['ativa'] and indicador_x - 15 <= n['x'] <= indicador_x + 45:
                        nota_valida = n
                        break

                if nota_valida:
                    iniciar_combate(nota_valida)
                else:
                    print("Sem nota valida de ataque, ataque falhou!")
            elif not em_combate:
                hero_index = destino
                hero_action = "walk"
                hero_frame = 0
                pontuacao += 10
                checar_zona()

        elif key == keys.RIGHT and hero_index == 4 and not em_combate:
            hero_action = "walk"
            hero_frame = 0
            pontuacao += 50
            iniciar_nova_fase()       

        elif key == keys.LEFT:
            hero_action = "defend"
            hero_frame = 0

#### Funcoes basicas ####
def update():
    global input_cooldown, chest_timer, chest_frame, hero_vida, estado_ritmo, estado_ritmo_timer, contador_notas, hero_defesa, ultimos_tipos 
        
    # Se esta no bau pausa o game
    if estado_bau:
        # Atualiza cooldown de input para evitar travar controles
        if input_cooldown > 0:
            input_cooldown -= 1

        # mantendo algumas animacoes
        chest_timer += 1
        if chest_timer >= chest_speed:
            chest_timer = 0
            chest_frame = (chest_frame + 1) % len(chest_idle_frames)

        update_hero()
        mover_heroi_suave()

        for inimigo in inimigos.values():
            inimigo['timer'] += 1
            if inimigo['estado'] == 'idle':
                if inimigo['timer'] >= 6:
                    inimigo['timer'] = 0
                    inimigo['frame'] = (inimigo['frame'] + 1) % len(enemy_idle_frames)

        return

    contador_notas += 1
    if contador_notas >= batida:
        contador_notas = 0

        # Verifica repetição
        if len(ultimos_tipos) >= 3 and all(t == ultimos_tipos[-1] for t in ultimos_tipos[-3:]):
            # Se as 3 ultimas notas forem iguais troca
            tipo = 'defesa' if ultimos_tipos[-1] == 'ataque' else 'ataque'
        else:
            tipo = random.choices(['ataque', 'defesa'], weights=[70, 30])[0]

        spawn_nota_ritmica(tipo)
        ultimos_tipos.append(tipo)

        if len(ultimos_tipos) > 5:
            ultimos_tipos.pop(0)
        
    if not jogo_ativo:
        return

    if input_cooldown > 0:
        input_cooldown -= 1

    if game_state == 'jogo':
        update_hero()
        mover_heroi_suave()

        # Atualiza notas 
        for nota in notas_ritmicas:
            if nota['atraso'] > 0:
                nota['atraso'] -= 1
                continue

            if nota['ativa']:
                # Movimenta a nota
                if nota['tipo'] == 'ataque':
                    nota['x'] -= velocidade_nota
                else:
                    nota['x'] += velocidade_nota

                # Verifica se esta na janela e ainda nao foi processada
                if (nota['tipo'] == 'defesa' and not nota['verificado']
                    and indicador_x - 25 <= nota['x'] <= indicador_x + 15):

                    nota['verificado'] = True  # Garante que essa nota nao causa mais de um hit
                    nota['pronta_para_ataque'] = True

                # Se a nota chegou bem no centro, remove da tela
                if abs(nota['x'] - indicador_x) < 5:
                    nota['ativa'] = False

                # limpa se sair da tela, mais uma seguranca mesmo
                if nota['x'] < -50 or nota['x'] > WIDTH + 50:
                    nota['ativa'] = False

        # Animação do bau
        chest_timer += 1
        if chest_timer >= chest_speed:
            chest_timer = 0
            chest_frame = (chest_frame + 1) % len(chest_idle_frames)

        # Resetar indicador apos alguns frames
        if estado_ritmo != 0:
            estado_ritmo_timer += 1
            if estado_ritmo_timer >= 10:
                estado_ritmo = 0
                estado_ritmo_timer = 0

        # Atualizar inimigos
        for index, inimigo in inimigos.items():
            inimigo['timer'] += 1

            # Animacoes normais
            if inimigo['estado'] == 'idle':
                if inimigo['timer'] >= 6:
                    inimigo['timer'] = 0
                    inimigo['frame'] = (inimigo['frame'] + 1) % len(enemy_idle_frames)

            elif inimigo['estado'] == 'hit':
                if inimigo['timer'] >= 5:
                    inimigo['timer'] = 0
                    inimigo['frame'] += 1
                    if inimigo['frame'] >= len(enemy_hit_frames):
                        inimigo['estado'] = 'idle'
                        inimigo['frame'] = 0

            elif inimigo['estado'] == 'dead':
                if inimigo['frame'] < len(enemy_die_frames) - 1:
                    if inimigo['timer'] >= 5:
                        inimigo['timer'] = 0
                        inimigo['frame'] += 1

            elif inimigo['estado'] == 'attack':
                # Animacao de ataque
                if inimigo['timer'] >= 5:
                    inimigo['timer'] = 0
                    inimigo['frame'] += 1
                    if inimigo['frame'] >= len(enemy_attack_frames):
                        inimigo['estado'] = 'idle'
                        inimigo['frame'] = 0

            # Ataca se o heroi estiver na zona anterior ao inimigo
            if index == hero_index + 1 and inimigo['estado'] != 'dead':
                nota_defesa_pronta = None
                for nota in notas_ritmicas:
                    if (nota['tipo'] == 'defesa' and nota.get('pronta_para_ataque', False) 
                        and nota['ativa']):
                        nota_defesa_pronta = nota
                        break

                if nota_defesa_pronta and inimigo['estado'] != 'attack':
                    inimigo['estado'] = 'attack'
                    inimigo['frame'] = 0
                    inimigo['timer'] = 0

                    dano = random.randint(5, 15)

                    # Armazena o valor antes da redução
                    defesa_original = hero_defesa

                    # Diminui 1 ponto de escudo
                    if hero_defesa > 0:
                        hero_defesa -= 1

                    if nota_defesa_pronta.get('defendido', False):
                        dano_recebido = max(0, dano - defesa_original)
                        print(f"DEFESA BEM SUCEDIDA! Dano sorteado: {dano}. Defesa original: {defesa_original}. Dano final: {dano_recebido}")
                    else:
                        dano_recebido = dano
                        print(f"DEFESA FALHOU! Dano sorteado: {dano}. Defesa original: {defesa_original}. Dano recebido: {dano_recebido}")

                    hero_vida -= dano_recebido

                    # Nota usada, desativa para evitar duplo dano
                    nota_defesa_pronta['ativa'] = False
                    nota_defesa_pronta['pronta_para_ataque'] = False

                    if hero_vida <= 0:
                        game_over()

def game_over():
    global jogo_ativo, game_state, recorde, pontuacao
    print("Game Over")
    if pontuacao > recorde:
        recorde = pontuacao
    jogo_ativo = False
    game_state = 'gameover'
    music.stop()

def start_game():
    global game_state, zonas, hero_index, hero_pos_x, hero_vida, em_combate, jogo_ativo, inimigos, hero_defesa, hero_dano, pontuacao
    pontuacao = 0
    #  Resetar status do herói
    hero_defesa = 5
    hero_dano = 10

    game_state = 'jogo'
    zonas = gerar_zonas()
    inicializar_inimigos()  # cria inimigos com base em zonas

    hero_index = 0
    hero_pos_x = ZONA_LARGURA // 2

    hero_vida = 100
    hero_defesa = 5
    hero_dano = 10
    em_combate = False
    jogo_ativo = True

    music.play("fundo")
    music.set_volume(volume if not muted else 0)

music.play("fundo")
music.set_volume(volume if not muted else 0)
pgzrun.go()