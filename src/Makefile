TARGET = funtetris
OBJS = main.o j2me_runtime.o j2me_gfx.o

LIBS = -lpspgu -lpspgum

EXTRA_TARGETS = EBOOT.PBP
PSP_EBOOT_TITLE = funtetris

PSPSDK = $(shell psp-config --pspsdk-path)
include $(PSPSDK)/lib/build.mak
