# Template de Traducao Bytecode -> C

## Instrucoes pra IA (eu)

1. Leia o .txt do metodo
2. Identifique:
   - Parametros (do descritor)
   - Variaveis locais (iload_N, istore_N)
   - Chamadas de API (invokevirtual Graphics.* -> j2me_gfx_*)
   - Estrutura de controle (if/goto -> while/if)
3. Gere C limpo com:
   - Assinatura correta (void* self, args)
   - Cast ((Classe_s*)self) quando acessar campo
   - Comentarios explicando o que faz

## Mapeamento de API

| J2ME | C |
|------|---|
| Graphics.setColor | j2me_gfx_set_color |
| Graphics.fillRect | j2me_gfx_fill_rect |
| Graphics.drawImage | j2me_image_blit |
| Graphics.drawRegion | j2me_image_draw_region |
| Canvas.repaint | j2me_canvas_repaint |
| Canvas.getGameAction | j2me_input_get_actions |
| Thread.sleep | j2me_sleep |
| Random.nextInt | j2me_random_next |

## Mapeamento de Controle

| Bytecode | C |
|----------|---|
| if_icmpeq + goto | if (a == b) { ... } |
| goto pra tras | while (cond) { ... } |
| goto pra frente | if + } |
| tableswitch | switch/case |
