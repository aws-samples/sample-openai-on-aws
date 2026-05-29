
"""
Math MCP Server

This module implements a Model Context Protocol (MCP) server that provides mathematical
capabilities to AI assistants. The server exposes tools for basic arithmetic operations,
prompts for mathematical assistance, and resources for configuration and greetings.

Features:
- Mathematical tools: addition, subtraction, multiplication, and division operations
- Prompts: math assistant and system prompts for AI interactions
- Resources: personalized greetings and application configuration

The server runs via stdio and can be integrated with MCP-compatible AI systems
to extend their mathematical reasoning capabilities.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")

# Prompts
@mcp.prompt(title='Example Prompt')
def example_prompt(question: str) -> str:
    """ math assistant prompt with detailed problem-solving guidance"""
    return f"""
    You are an expert mathematics assistant with access to computational tools.
    
    Your approach to solving mathematical problems:
    1. Read and understand the question carefully
    2. Break down complex problems into smaller steps
    3. Use available tools (add, subtract, multiply, divide) for accurate calculations
    4. Show your work clearly with step-by-step reasoning
    5. Verify your answer and explain the solution method
    
    Question to solve: {question}
    
    Please provide a detailed solution with clear explanations of your mathematical reasoning.
    If calculations are needed, use the appropriate tools to ensure accuracy.
    """

@mcp.prompt(title='System Prompt')
def system_prompt() -> str:
    """System prompt for mathematical AI assistant with tool usage guidance"""
    return """
    You are an AI assistant specialized in mathematical operations and problem-solving.
    
    
    When users ask mathematical questions:
    1. Use the appropriate tools for calculations when needed
    2. Show your work step by step
    3. Provide clear explanations of mathematical concepts
    4. Double-check your calculations using the available tools
    
    Always prioritize accuracy and clarity in your mathematical responses.
    """

# Tools
@mcp.tool(title='Add tool')
def add(a: int, b: int) -> int:
    """
    Performs addition of two integers with validation and error handling.
    
    This tool computes the sum of two integer values and returns the result.
    It's designed for accurate arithmetic operations in mathematical problem-solving.
    
    Args:
        a (int): The first integer operand (addend)
        b (int): The second integer operand (addend)
    
    Returns:
        int: The sum of a and b (a + b)
    
    Examples:
        add(5, 3) -> 8
        add(-2, 7) -> 5
        add(0, 100) -> 100
    
    Use this tool when you need to:
    - Calculate sums in mathematical expressions
    - Verify addition operations step-by-step
    - Ensure accuracy in arithmetic computations
    """
    return a + b

@mcp.tool(title='Multiply tool')
def multiply(a: int, b: int) -> int:
    """
    Performs multiplication of two integers with comprehensive documentation.
    
    This tool computes the product of two integer values and returns the result.
    It's essential for scaling, area calculations, and complex mathematical operations.
    
    Args:
        a (int): The first integer operand (multiplicand)
        b (int): The second integer operand (multiplier)
    
    Returns:
        int: The product of a and b (a × b)

    
    Examples:
        multiply(4, 7) -> 28
        multiply(-3, 5) -> -15
        multiply(0, 999) -> 0
        multiply(12, 1) -> 12
    
    Use this tool when you need to:
    - Calculate products in mathematical expressions
    - Compute areas, volumes, or scaling operations
    - Verify multiplication operations step-by-step
    - Handle repeated addition scenarios efficiently
    """
        
    return a*b
    

@mcp.tool(title='Subtract tool')
def subtract(a: int, b: int) -> int:
    """
    Performs subtraction of two integers with validation and error handling.
    
    This tool computes the difference between two integer values and returns the result.
    It's essential for calculating differences, distances, and inverse operations.
    
    Args:
        a (int): The minuend (number being subtracted from)
        b (int): The subtrahend (number being subtracted)
    
    Returns:
        int: The difference of a and b (a - b)

    
    Examples:
        subtract(10, 3) -> 7
        subtract(5, 8) -> -3
        subtract(-2, -7) -> 5
        subtract(100, 0) -> 100
    
    Use this tool when you need to:
    - Calculate differences in mathematical expressions
    - Find distances between values
    - Perform inverse addition operations
    - Verify subtraction operations step-by-step
    """

    return a-b

@mcp.tool(title='Divide tool')
def divide(a: int, b: int) -> float:
    """
    Performs division of two integers with comprehensive error handling.
    
    This tool computes the quotient of two integer values and returns a float result.
    
    
    Args:
        a (int): The dividend (number being divided)
        b (int): The divisor (number dividing by)
    
    Returns:
        float: The quotient of a and b (a ÷ b)
    
   
    
    Examples:
        divide(10, 2) -> 5.0
        divide(7, 3) -> 2.3333333333333335
        divide(-15, 3) -> -5.0
        divide(0, 5) -> 0.0
    
    Use this tool when you need to:
    - Calculate quotients in mathematical expressions
    - Perform ratio and proportion calculations
    - Convert between units with scaling factors
    - Verify division operations step-by-step
    """
    
    return a/b

if __name__ == "__main__":
    print('Starting MCP Server...')
    mcp.run()  # Run server via stdio