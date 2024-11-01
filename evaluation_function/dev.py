import sys

from lf_toolkit.shared.params import Params

try:
    from .evaluation import evaluation_function
except ImportError:
    from evaluation_function.evaluation import evaluation_function

def dev():
    """Run the evaluation function from the command line for development purposes.

    Usage: python -m evaluation_function.dev <answer> <response>
    """
    if len(sys.argv) < 3:
        print("Usage: python -m evaluation_function.dev <answer> <response>")
        return
    
    answer = sys.argv[1]
    response = sys.argv[2]

    result = evaluation_function(answer, response, Params())

    print(result)

if __name__ == "__main__":
    dev()