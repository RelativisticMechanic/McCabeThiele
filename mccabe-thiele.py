import engine2D
import numpy

screen_w = 960
screen_h = 960
screen_factor = 1

GRAPH_OFFSET_X = screen_w / 100
GRAPH_OFFSET_Y = screen_h / 100

EFFECTIVE_SCREEN_W = (screen_w - 2 * GRAPH_OFFSET_X)
EFFECTIVE_SCREEN_H = (screen_h - 2 * GRAPH_OFFSET_Y)

# The parameters to be used for the McCabe-Thiele Problem
x_D = 0.9
x_F = 0.6
x_W = 0.1
reflux_ratio = 4
q = 0.65
stages = 0
#equilibrium_data = [(0,0),(1,1)]
equilibrium_data = [(0,0), (0.13, 0.261), (0.258, 0.456), (0.411, 0.632), (0.581, 0.777), (0.78, 0.90), (1,1)]

precision = 0.05

def request_data():
    global reflux_ratio, x_D, x_W, x_F, q
    reflux_ratio = float(input("The Reflux-Ratio of the Column (R): "))
    x_D = float(input("The distillate mole fraction (x_D): "))
    x_F = float(input("The feed mole fraction (x_F): "))
    x_W = float(input("The bottom product mole fraction (x_W): "))
    q = float(input("The quality-factor (Q) of the feed: "))

    print("Enter the equilibrium mole fractions x,y (separated by a COMMA). If you wish to stop, simply press ENTER")
    while True:
        inpt =  input("x,y: ")
        if(inpt == ""):
            break
        equilibrium_data.append([float(x) for x in inpt.split(",")])
    
    # sort equilibrium data by x-coordinate 
    equilibrium_data = sorted(equilibrium_data, key=lambda x: x[0])

# Enriching section operating line generation function
def esol(x):
    return (reflux_ratio/(reflux_ratio+1))*x + x_D/(reflux_ratio+1)

# Feed line
def qol(x):
    return (q/(q-1)*x - x_F/(q-1))

# Stripping section operating line generation function
def ssol(x):
    x_i = intersect_qeol()
    return (qol(x_i) - x_W)/(x_i - x_W)*(x - x_W) + x_W

# el - The equilibrium line to be generated from data
def el(x):
    for i in range(0, len(equilibrium_data)):
        if(x <= equilibrium_data[i][0]):
            # Linear interpolation
            x1 = equilibrium_data[i-1][0]
            x2 = equilibrium_data[i][0]
            y1 = equilibrium_data[i-1][1]
            y2 = equilibrium_data[i][1]

            return ((y2 - y1)/(x2 - x1)) * (x - x1) + y1

# The inverse function of the equilibrium line
# el - The equilibrium line to be generated from data
def el_inverse(y):
    for i in range(0, len(equilibrium_data)):
        if(y <= equilibrium_data[i][1]):
            x1 = equilibrium_data[i-1][0]
            x2 = equilibrium_data[i][0]
            y1 = equilibrium_data[i-1][1]
            y2 = equilibrium_data[i][1]
            return ((x2 - x1)/(y2 - y1))*(y-y1) + x1
    return 1

# The intersection point of the q-line and the eol
# EOL == (R/R+1)x + x_D/R+1
# Q == (q/q-1)x - x_F/q-1
def intersect_qeol():
    return (-(x_D/(reflux_ratio+1)) - (x_F/(q-1))) / ((reflux_ratio/(reflux_ratio+1) - (q/(q-1)))) 

# x and y lie between [0, 1]
def graph_to_screen(x,y):
    return (GRAPH_OFFSET_X + x * EFFECTIVE_SCREEN_W, EFFECTIVE_SCREEN_H - y * EFFECTIVE_SCREEN_H + GRAPH_OFFSET_Y)

# some quick and dirty functions that convert to screen coordinates and draw the line
def draw_line(p1, p2, col=(255, 255, 255), w=1):
    p1_ = graph_to_screen(p1[0], p1[1])
    p2_ = graph_to_screen(p2[0], p2[1])
    engine2D.DrawLine(p1_[0], p1_[1], p2_[0], p2_[1], col[0], col[1], col[2], w)

def draw_axes():
    draw_line((0,0), (0,1))
    draw_line((0,0), (1,0))

    # draw y=x line
    draw_line((0,0), (1,1), w=2)

def mc_cabe_thiele():
    global stages
    crossed_feed = False
    y_prev = x_D
    x_prev = x_D
    x_new = x_D
    y_prev = x_D
    stages = 0

    while(x_new > x_W):
        x_new = el_inverse(y_prev)
        # Draw the horizontal line
        draw_line((x_prev, y_prev), (x_new, y_prev))

        if(x_new <= x_F):
            crossed_feed = True
        
        if(crossed_feed == False):
            draw_line((x_new, y_prev), (x_new, esol(x_new)))
            y_prev = esol(x_new)
        else:
            draw_line((x_new, y_prev), (x_new, ssol(x_new)))
            y_prev = ssol(x_new)
        
        if(x_prev == x_new):
            break
        x_prev = x_new
        stages += 1

class Renderer(engine2D.Object):

    def Draw(self, elapsed):
        engine2D.Clear(32, 32, 32)
        draw_axes()

        # draw equilibrium line
        x_prev = 0
        for x in numpy.arange(0+precision, 1+precision, precision):
            draw_line((x_prev, el(x_prev)), (x, el(x)), (32, 32, 192), w=2)
            x_prev = x
        
        # draw the esol
        draw_line((x_D, x_D), (intersect_qeol(), esol(intersect_qeol())), (192, 32, 32), w=2)
        # draw the feed
        draw_line((x_F, x_F), (intersect_qeol(), esol(intersect_qeol())), (192, 192, 32), w=2)
        # draw ssol
        draw_line((x_W, x_W), (intersect_qeol(), esol(intersect_qeol())), (192, 32, 192), w=2)

        # mc-cabe thiele
        mc_cabe_thiele()

class Menu(engine2D.Object):

    def Create(self):
        self.fnt = engine2D.BitmapFont("./cp8x16.png", 8, 16, ch_offset=32)
    
    def Draw(self, elapsed):
        self.fnt.PutString("Reflux Ratio: " + str(reflux_ratio) + " Stages Required: " + str(stages), 30, 0)
        self.fnt.PutString("Press LEFT to decrease reflux ratio, press RIGHT to increase reflux ratio", 30, 16)
    def OnKeyPress(self, elapsed, key):
        global reflux_ratio
        if(key == engine2D.Button.LEFT):
            reflux_ratio -= 0.25
        elif(key == engine2D.Button.RIGHT):
            reflux_ratio += 0.25

print(el_inverse(esol(el_inverse(x_D))))
engine2D.Init(screen_w, screen_h, screen_w * screen_factor, screen_h * screen_factor)
engine2D.AddObject(Renderer())
engine2D.AddObject(Menu())
engine2D.SetCaption("McCabe-Thiele Calculation")
engine2D.Loop(60)