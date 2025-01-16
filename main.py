import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
import numpy as np
import os
import tkinter as tk
from tkinter import ttk

class StarPhysics:
    def __init__(self, initial_mass, h2_percentage):
        self.initial_mass = initial_mass  # Mass in solar masses
        self.current_mass = initial_mass
        self.h2_percentage = h2_percentage  # Initial H2 percentage
        self.current_h2 = h2_percentage
        self.age = 0
        self.luminosity = 0
        self.temperature = 0
        self.radius = 0
        self.initial_radius = 0  # Store initial radius for reference
        self.stage = "Protostar"
        self.expansion_factor = 1.0  # New variable to track expansion
        
        # Constants (simplified stellar evolution parameters)
        self.SOLAR_MASS = 1.989e30  # kg
        self.SOLAR_RADIUS = 6.957e8  # meters
        self.SOLAR_LUMINOSITY = 3.828e26  # watts
        
        self.update_stellar_properties()
        self.initial_radius = self.radius  # Save initial radius after first calculation

    def update_stellar_properties(self):
        """Calculate star properties based on mass and H2 content"""
        # Mass-luminosity relation (simplified)
        if self.current_mass < 0.43:
            self.luminosity = 0.23 * (self.current_mass ** 2.3)
        elif self.current_mass < 2:
            self.luminosity = (self.current_mass ** 4)
        else:
            self.luminosity = 1.4 * (self.current_mass ** 3.5)
        
        # Temperature calculation (simplified)
        self.temperature = 5778 * (self.luminosity ** 0.25)  # Kelvin
        
        # Calculate base radius
        base_radius = self.calculate_base_radius()
        
        # Apply expansion factor based on stage
        self.radius = base_radius * self.expansion_factor
        
        # Update evolutionary stage
        self.determine_stage()
        
        # Update expansion factor based on stage
        self.update_expansion_factor()
    
    def calculate_base_radius(self):
        """Calculate the base radius before applying expansion factors"""
        if self.current_mass < 1.0:
            return self.current_mass ** 0.8
        else:
            return self.current_mass ** 0.57

    def update_expansion_factor(self):
        """Update the expansion factor based on stellar evolution stage"""
        if self.stage == "Protostar":
            # Protostar starts large and contracts
            time_factor = min(1.0, self.age / self.get_formation_time())
            self.expansion_factor = 2.0 - time_factor
        
        elif self.stage == "Main Sequence":
            # Gradual expansion during main sequence
            ms_lifetime = self.get_main_sequence_lifetime()
            if ms_lifetime > 0:
                progress = min(1.0, self.age / ms_lifetime)
                self.expansion_factor = 1.0 + (progress * 0.5)
        
        elif self.stage == "Red Giant":
            # Dramatic expansion in red giant phase
            target_expansion = 100 if self.initial_mass > 1.44 else 50
            current_expansion = self.expansion_factor
            # Smooth transition to red giant size
            self.expansion_factor = min(target_expansion, 
                                     current_expansion + 0.1)
        
        elif self.stage == "White Dwarf":
            # Rapid contraction to white dwarf size
            self.expansion_factor = max(0.01, self.expansion_factor * 0.95)
        
        elif self.stage == "Supernova":
            # Explosive expansion
            self.expansion_factor *= 1.5

    def determine_stage(self):
        """Determine star's evolutionary stage based on mass and H2 content"""
        old_stage = self.stage
        
        if self.age < self.get_formation_time():
            new_stage = "Protostar"
        elif self.current_h2 > 0.1:
            new_stage = "Main Sequence"
        elif self.current_mass > 1.44:  # Chandrasekhar limit
            if old_stage != "Supernova":
                new_stage = "Red Giant"
            else:
                new_stage = "Supernova"
        elif self.current_h2 <= 0.1 and old_stage != "White Dwarf":
            new_stage = "Red Giant"
        else:
            new_stage = "White Dwarf"
        
        # If stage has changed, handle the transition
        if old_stage != new_stage:
            self.handle_stage_transition(old_stage, new_stage)
        
        self.stage = new_stage

    def handle_stage_transition(self, old_stage, new_stage):
        """Handle special cases during stage transitions"""
        if old_stage == "Main Sequence" and new_stage == "Red Giant":
            # Initial expansion burst when entering red giant phase
            self.expansion_factor *= 2.0
        elif new_stage == "Supernova":
            # Immediate explosive expansion
            self.expansion_factor *= 10.0

    def get_formation_time(self):
        """Calculate formation time based on mass"""
        return 50000 * (1 / self.initial_mass)  # Simplified timescale

    def update(self, delta_time):
        """Update star's properties over time"""
        self.age += delta_time
        
        # H2 consumption rate (simplified)
        if self.stage == "Main Sequence":
            h2_consumption_rate = 0.1 * (self.current_mass ** 3.5) / 1e10
            self.current_h2 -= h2_consumption_rate * delta_time
            self.current_h2 = max(0, self.current_h2)
        
        # Mass loss in late stages
        if self.stage == "Red Giant":
            mass_loss_rate = 1e-11 * self.current_mass
            self.current_mass -= mass_loss_rate * delta_time
        
        self.update_stellar_properties()
    def get_color(self):
        """Calculate star color based on temperature"""
        # Simplified blackbody color approximation
        temp = self.temperature
        if temp < 3500:
            return (1.0, 0.0, 0.0)  # Red
        elif temp < 5000:
            return (1.0, 0.5, 0.0)  # Orange
        elif temp < 6000:
            return (1.0, 1.0, 0.0)  # Yellow
        elif temp < 7500:
            return (1.0, 1.0, 1.0)  # White
        else:
            return (0.8, 0.8, 1.0)  # Blue-white

    def get_emission(self):
        """Calculate emission based on luminosity"""
        return min(1.0, 0.2 + (np.log10(self.luminosity) / 5))

    def get_main_sequence_lifetime(self):
        """Calculate main sequence lifetime based on mass and H2 content"""
        return 1e10 * (self.initial_mass ** -2.5) * (self.h2_percentage / 71)

def get_user_input():
    """Create GUI window for user input"""
    root = tk.Tk()
    root.title("Star Parameters")
    
    # Variables to store user input
    mass_var = tk.DoubleVar(value=1.0)
    h2_var = tk.DoubleVar(value=71.0)
    
    # Create and pack widgets
    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    ttk.Label(frame, text="Star Mass (solar masses):").grid(row=0, column=0, padx=5, pady=5)
    ttk.Entry(frame, textvariable=mass_var).grid(row=0, column=1, padx=5, pady=5)
    
    ttk.Label(frame, text="Initial H2 Percentage:").grid(row=1, column=0, padx=5, pady=5)
    ttk.Entry(frame, textvariable=h2_var).grid(row=1, column=1, padx=5, pady=5)
    
    # Variables to store the result
    result = {"mass": None, "h2": None}
    
    def on_submit():
        result["mass"] = mass_var.get()
        result["h2"] = h2_var.get()
        root.destroy()
    
    ttk.Button(frame, text="Start Simulation", command=on_submit).grid(row=2, column=0, columnspan=2, pady=10)
    
    root.mainloop()
    return result["mass"], result["h2"]

def generate_star_texture(size=256):
    texture = np.zeros((size, size, 4), dtype=np.uint8)
    center = size // 2
    max_radius = size // 2
    
    for x in range(size):
        for y in range(size):
            dx = x - center
            dy = y - center
            distance = np.sqrt(dx*dx + dy*dy)
            
            # Base gradient
            intensity = max(0, 1 - (distance / max_radius))
            
            # Surface features
            noise = np.random.rand() * 0.2
            pattern = (np.sin(x / 8.0) * np.cos(y / 8.0) * 0.1 + 
                      np.sin((x + y) / 16.0) * 0.1)
            
            # Combine effects
            value = min(1.0, max(0.0, intensity + noise + pattern))
            brightness = int(value * 255)
            alpha = int(intensity * 255)
            
            texture[x, y] = [brightness, brightness, brightness, alpha]
    
    return texture

def load_texture():
    texture_data = generate_star_texture()
    image_data = texture_data.tobytes()
    width = height = texture_data.shape[0]

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    return texture_id

def draw_sphere(radius, color, emission, texture_id):
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture_id)

    ambient = [x * 0.1 for x in color]
    diffuse = [x * 0.3 for x in color]
    emission_color = [x * emission for x in color]

    glMaterialfv(GL_FRONT, GL_AMBIENT, [*ambient, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [*diffuse, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.2, 0.2, 0.2, 1.0])
    glMaterialfv(GL_FRONT, GL_EMISSION, [*emission_color, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 10.0)

    quad = gluNewQuadric()
    gluQuadricTexture(quad, GL_TRUE)
    gluQuadricNormals(quad, GLU_SMOOTH)
    gluSphere(quad, radius, 64, 64)
    gluDeleteQuadric(quad)

    glDisable(GL_TEXTURE_2D)

def render_text(screen, star):
    text_surface = pygame.Surface((800, 600), pygame.SRCALPHA)
    font = pygame.font.Font(None, 36)
    
    # Star information
    info_lines = [
        f"Stage: {star.stage}",
        f"Mass: {star.current_mass:.2f} solar masses",
        f"Temperature: {star.temperature:.0f} K",
        f"Luminosity: {star.luminosity:.2f} solar luminosity",
        f"Radius: {star.radius:.2f} solar radius",
        f"H2 Remaining: {star.current_h2:.1f}%",
        f"Age: {star.age:.0f} years"
    ]
    
    for i, line in enumerate(info_lines):
        text_surface.blit(
            font.render(line, True, (255, 255, 255)),
            (10, 10 + i * 30)
        )
    
    screen.blit(text_surface, (0, 0))

def main():
    # Get initial star parameters from user
    mass, h2_percentage = get_user_input()
    
    pygame.init()
    width, height = 800, 600
    
    screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pygame_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    pygame.display.set_caption("Physical Star Lifecycle Simulation")

    gluPerspective(45, (width / height), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 2.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.3, 0.3, 0.3, 1.0])
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.05, 0.05, 0.05, 1.0])

    clock = pygame.time.Clock()
    texture_id = load_texture()
    star = StarPhysics(mass, h2_percentage)
    angle = 0
    
    time_acceleration = 1e3  # Simulation speed multiplier

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                return
            elif event.type == KEYDOWN:
                if event.key == K_UP:
                    time_acceleration *= 2
                elif event.key == K_DOWN:
                    time_acceleration /= 2

        delta_time = clock.get_time() / 1000 * time_acceleration
        star.update(delta_time)

        # Clear the screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.0, 0.0, 0.02, 1.0)

        # Draw 3D scene
        glPushMatrix()
        glRotatef(angle, 0, 1, 0)
        
        # Get star properties for visualization
        visual_radius = np.log1p(star.radius) * 0.8  # Logarithmic scale for better visualization
        color = star.get_color()
        emission = star.get_emission()
        
        draw_sphere(visual_radius, color, emission, texture_id)
        glPopMatrix()

        # Switch to 2D mode for text
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Disable 3D features for text rendering
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        # Render text
        pygame_surface.fill((0, 0, 0, 0))
        render_text(pygame_surface, star)
        
        # Convert Pygame surface to OpenGL texture
        text_data = pygame.image.tostring(pygame_surface, 'RGBA', True)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDrawPixels(width, height, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        glDisable(GL_BLEND)

        # Restore 3D mode
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        pygame.display.flip()
        clock.tick(60)
        angle += 1

if __name__ == "__main__":
    main()