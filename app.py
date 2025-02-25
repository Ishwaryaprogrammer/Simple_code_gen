from flask import Flask, render_template, request, jsonify
import re
import os

app = Flask(__name__, template_folder="templates")

# Function to generate assembly-like instructions for arithmetic expressions
def generate_instructions(expression):
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*(.*)$'
    
    # Check for valid expression format
    if not re.match(pattern, expression):
        return "Error: Invalid expression format. Please use the format: variable = operand1 operator operand2"

    variable, expr = expression.split('=')
    variable = variable.strip()
    expr = expr.strip()

    # Tokenizing the expression
    tokens = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*|\d+|[+\-*\/%()])', expr)

    # Check for empty expressions
    if not tokens:
        return "Error: Empty expression provided."

    # Handle stack for the expression
    stack = []
    instructions = []
    register_count = 0

    # Precedence rules
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2}

    def process_operator(op, right, left):
        nonlocal register_count
        instructions.append(f"LOAD R{register_count}, {left}")
        if op == '+':
            instructions.append(f"ADD R{register_count}, {right}")
        elif op == '-':
            instructions.append(f"SUB R{register_count}, {right}")
        elif op == '*':
            instructions.append(f"MUL R{register_count}, {right}")
        elif op == '/':
            instructions.append(f"DIV R{register_count}, {right}")
        elif op == '%':
            instructions.append(f"MOD R{register_count}, {right}")
        return f"R{register_count}"

    # Evaluate the expression using Shunting Yard Algorithm
    output_queue = []
    operator_stack = []

    for token in tokens:
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', token) or re.match(r'^\d+$', token):
            output_queue.append(token)
        elif token in precedence:
            while (operator_stack and operator_stack[-1] in precedence and
                   precedence[token] <= precedence[operator_stack[-1]]):
                output_queue.append(operator_stack.pop())
            operator_stack.append(token)
        elif token == '(':
            operator_stack.append(token)
        elif token == ')':
            while operator_stack and operator_stack[-1] != '(':
                output_queue.append(operator_stack.pop())
            operator_stack.pop()  # Pop the '('

    while operator_stack:
        output_queue.append(operator_stack.pop())

    # Generate instructions
    for token in output_queue:
        if token in precedence:
            if len(stack) < 2:
                return "Error: Insufficient operands for operation."
            right = stack.pop()
            left = stack.pop()
            result = process_operator(token, right, left)
            stack.append(result)
            register_count += 1
        else:
            stack.append(token)

    # Final check for stored variable
    if len(stack) == 1:
        instructions.append(f"STORE {variable}, {stack[0]}")
    else:
        return "Error: Invalid expression format."

    return '\n'.join(instructions)

# Route to serve the HTML page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle form submission
@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    expression = data.get('expression', '')

    # Generate the assembly-like instructions
    instructions = generate_instructions(expression)

    return jsonify({'instructions': instructions})

port = int(os.environ.get("PORT", 10000))  
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
