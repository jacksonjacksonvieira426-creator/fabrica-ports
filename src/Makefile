TARGET = cod_psp
OBJS = main.o j2me_runtime.o j2me_gfx.o j2me_font.o j2me_input.o \
       j2me_image.o j2me_clip.o j2me_vector.o j2me_string.o j2me_rms.o

EXTRA_TARGETS = EBOOT.PBP
PSP_EBOOT_TITLE = cod_psp

PSPSDK = $(shell psp-config --pspsdk-path)
include $(PSPSDK)/lib/build.mak
