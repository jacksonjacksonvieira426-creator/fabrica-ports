#ifndef J2ME_INPUT_H
#define J2ME_INPUT_H

#define J2ME_UP     1
#define J2ME_DOWN   2
#define J2ME_LEFT   4
#define J2ME_RIGHT  8
#define J2ME_FIRE   16

void j2me_input_init(void);
void j2me_input_update(void);
int  j2me_input_get_actions(void);
char j2me_input_get_key(void);
int  j2me_input_is_pressed(int action);
int  j2me_input_is_down(int action);
int  j2me_input_should_quit(void);

#endif
