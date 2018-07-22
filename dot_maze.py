import copy
import pygame
import random
import time
import math

class Player:
    
    def __init__(self, x, y, size):
        self.brain = self.create_brain(size)
        self.x = x
        self.y = y
        self.vel = [0,0]
        self.max_vel = 5
        self.size = size
        self.index = 0
        self.alive = True
        self.fitness = 0
        self.num_steps = 0
        
    def create_brain(self, size):
        return [(random.randint(-1,1), random.randint(-1,1)) for x in range(size)]

    def move(self, width, height, offset, walls, goal):
        if not self.alive:
            return
        a = self.brain[self.index]
        self.vel[0] += a[0]
        if self.vel[0] > self.max_vel:
            self.vel[0] = self.max_vel
        self.vel[1] += a[1]
        if self.vel[1] > self.max_vel:
            self.vel[1] = self.max_vel
        self.x += self.vel[0]
        w = self.get_collision(width, height, walls, offset)
        if w is not None:
            if self.vel[0] > 0:
                self.x = w.x//offset
            else:
                self.x = (w.x+w.width)//offset - offset
        self.y += self.vel[1]
        w = self.get_collision(width, height, walls, offset)
        if w is not None:
            if self.vel[1] > 0:
                self.y = w.y//offset
            else:
                self.y = (w.y+w.height)//offset - offset
        self.index += 1
        self.num_steps += 1
        if self.index >= self.size or self.get_collision(width, height, walls, offset) is not None or self.x < 0 or self.y < 0 or self.x >= width or self.y >= height or self.x == goal[0] and self.y == goal[1]:
            self.alive = False
            self.fitness = 1/(1+(abs(self.x-goal[0])+abs(self.y-goal[1]))**2)
            if self.x == goal[0] and self.y == goal[1]:
                self.fitness += 1/(self.num_steps**2)
        
    def get_collision(self, width, height, walls, offset):
        for w in walls:
            if w.colliderect(pygame.Rect(self.x*offset,self.y*offset,offset,offset)):
                return w
        
class Game:

    def __init__(self, width, height, offset, start, goal, visualize=False):
        self.MUTATION_RATE = 0.1
        self.CROSSOVER_RATE = 0.3
        self.NUM_ELITES = 1
        self.POPULATION_SIZE = 100
        self.MAX_GENERATIONS = 100
        self.BRAIN_SIZE = 200
        
        self.width = width
        self.height = height
        self.offset = offset
        self.visualize = visualize
        self.walls = []
        self.players = []
        self.best_path = []
        for _ in range(self.POPULATION_SIZE):
            self.players.append(Player(start[0],start[1],self.BRAIN_SIZE))
        self.start = start
        self.goal = goal
        self.generation = 0
        
        wall = pygame.Rect(0,50 * offset, 75 * offset, 10 * offset)
        self.walls.append(wall)
        
        if visualize:
            pygame.init()
            self.screen = pygame.display.set_mode((self.width*self.offset,self.height*self.offset))
            self.screen.fill(pygame.Color('white'))
            pygame.display.set_caption('Maze')
            pygame.display.flip()
            
        self.reset()

    def run(self):
        while self.generation < self.MAX_GENERATIONS:
            while True:
                if self.visualize:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            exit()
                    time.sleep(0.05)
                if not self.check_alive():
                    break
                self.best_path.append((self.players[0].x,self.players[0].y))
                for p in self.players:
                    p.move(self.width, self.height, self.offset, self.walls, self.goal)
                self.draw()
            
            self.players = self.selection()
            for i in range(1,len(self.players)-1,2):
                if random.uniform(0,1) <= self.CROSSOVER_RATE:
                    self.crossover(self.players[i],self.players[i+1])
                self.mutate(self.players[i])
                self.mutate(self.players[i+1])               
            self.generation +=1
            self.reset()

    def draw(self):
        # reset screen
        self.screen.fill(pygame.Color('white'))
        # draw board
        for p in self.players:
            pygame.draw.rect(self.screen, pygame.Color('black'), pygame.Rect(p.x*self.offset,p.y*self.offset, self.offset, self.offset))
        for n in self.best_path:
            pygame.draw.rect(self.screen, pygame.Color('red'), pygame.Rect(n[0]*self.offset, n[1]*self.offset, self.offset, self.offset))
        for w in self.walls:
            pygame.draw.rect(self.screen, pygame.Color('black'), w, 1)
        pygame.draw.rect(self.screen, pygame.Color('green'), pygame.Rect(self.players[0].x*self.offset,self.players[0].y*self.offset, self.offset, self.offset))
        pygame.draw.rect(self.screen, pygame.Color('red'), pygame.Rect(self.goal[0]*self.offset,self.goal[1]*self.offset, self.offset, self.offset))
        pygame.display.flip()
        
    def check_alive(self):
        for p in self.players:
            if p.alive:
                return True
        return False

    def mutate(self, c):
        for i in range(self.BRAIN_SIZE):
            if random.uniform(0,1) <= self.MUTATION_RATE:
                c.brain[i] = (random.randint(-1,1), random.randint(-1,1))     
        
    def crossover(self, c1, c2):
        i = random.randint(0,c1.size)
        b1 = c1.brain[:i] + c2.brain[i:]
        b2 = c2.brain[:i] + c1.brain[i:]
        c1.brain = b1
        c2.brain = b2
        
    def selection(self):
        fit_sum = 0
        for c in self.players:
            fit_sum += c.fitness
        new_pop = []
        new_pop.append(self.selectBestPlayer())
        for _ in range(len(self.players)-1):
            n = random.uniform(0,fit_sum)
            for c in self.players:
                fit_sum -= c.fitness
                if fit_sum <= 0:
                    new_pop.append(copy.deepcopy(c))
                    break
        return new_pop
        
    def selectBestPlayer(self):
        best = self.players[0]
        for p in self.players:
            if p.fitness > best.fitness:
                best = p
        return best
    
    def reset(self):
        for p in self.players:
            p.x = self.start[0]
            p.y = self.start[1]
            p.fitness = 0
            p.index = 0
            p.alive = True
            p.num_steps = 0
            p.vel = [0,0]
        self.best_path = []
            
     
def main():
    
    width = 100
    height = 100
    offset = 5
    start = (50,10)
    goal = (50, 90)
    
    game = Game(width, height, offset, start, goal, True)
    game.run()
    
if __name__ == '__main__':
    main()
    