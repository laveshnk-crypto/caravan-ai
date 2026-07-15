# Convert all python files in this directory to txt files
import os

for filename in os.listdir('.'):
    if filename.endswith('.py'):
        with open(filename, 'r') as f:
                content = f.read()
        with open(filename[:-3] + '.txt', 'w') as f:
            f.write(content)