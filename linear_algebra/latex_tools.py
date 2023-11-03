import numpy as np

def augmented_matrix_to_latex(aug_matrix, operations):
    def add_matrix(aug_matrix):
        num_cols = len(aug_matrix[0])
        num_rows = len(aug_matrix)
        code_beginning = r"\left[\begin{array}{row_count|r}".replace('row_count', 'r' * (num_cols-1))
        code_ending = r"\end{array}\right]"
        latex_rows = []
        for row in aug_matrix:
            latex_row = ' & '.join([f'{coeff}' for coeff in row])
            latex_rows.append(latex_row)
        
        matrix_code = " \\\\ \n".join(latex_rows)
        
        return code_beginning + "\n" + matrix_code + "\n", code_ending
    
    def add_annotation(operations):
        # [("swap", row_1, row_2), ("add", row_2, row_3), ("scale", row_3, 2)]] 
        add_in_substack = []
        for operation in operations:
            op = operation[0]
            r1 = operation[1]
            r2 = operation[2]
            scale_factor = operation[3] if len(operation) == 4 else None
            
            if op == 'swap':
                add_in_substack.append(f'R_{r1} \\leftrightarrow R_{r2}')
            elif op == 'scale':
                add_in_substack.append(f'{scale_factor}R_{r1}')
            elif op == 'add' or op == 'subtract':
                operation_type = "-" if op == "subtract" else "+"
                
                if scale_factor == 1:
                    annotation = f'R_{r1} {operation_type} R_{r2}'
                else:
                    annotation = f'R_{r1} {operation_type} {scale_factor}R_{r2}'
                    
                add_in_substack.append(annotation)

        return r"\xrightarrow{\substack{" + r"\\\\".join(add_in_substack) + "}}\n"


    latex_code = add_annotation(operations) + add_matrix(aug_matrix)    
    print(latex_code)
    # # Perform any row operations
    # latex_transformations = []
    # for operation in operations:
    #     if operation[0] == 'swap':
    #         i, j = operation[1], operation[2]
    #         aug_matrix[i], aug_matrix[j] = aug_matrix[j], aug_matrix[i]
    #         latex_transformations.append(f'R_{i+1} \\leftrightarrow R_{j+1}')
    #     elif operation[0] == 'scale':
    #         i, c = operation[1], operation[2]
    #         aug_matrix[i] = [c * coeff for coeff in aug_matrix[i]]
    #         latex_transformations.append(f'{c:.2f}R_{i+1}')
    #     elif operation[0] == 'add':
    #         i, j, c = operation[1], operation[2], operation[3]
    #         aug_matrix[i] = [coeff1 + c * coeff2 for coeff1, coeff2 in zip(aug_matrix[i], aug_matrix[j])]
    #         latex_transformations.append(f'R_{i+1} \\leftarrow R_{i+1} + {c:.2f}R_{j+1}')
    #     # Add text implying what transformation was performed
    #     latex_rows.append(f'{operation[0]} {latex_transformations[-1]} to R_{operation[2]+1}')

    # # Convert the augmented matrix to LaTeX code again
    # latex_rows = []
    # for row in aug_matrix:
    #     latex_row = ' & '.join([f'{coeff:.2f}' if coeff != 0 else '0' for coeff in row[:-1]])
    #     latex_row += f' &= {row[-1]:.2f} \\\\'
    #     latex_rows.append(latex_row)

    # # Create the final LaTeX code for the system of linear equations
    # latex_eqs = []
    # for i, row in enumerate(latex_rows):
    #     latex_eq = f'{variable_names[i]}: {row}'
    #     latex_eqs.append(latex_eq)
    # latex_code = '\\\\\n'.join(latex_eqs)

    # return f'\\xrightarrow{{\\substack{{{chr(92)}\\\\\\\\{chr(92)}}}\n {chr(32).join(latex_transformations)}}}\n  \\left[\\begin{{array}}{{{"r" * (len(aug_matrix[0])-1)}"|r"}}\\right]\n  {chr(92)}\\\\\n'.join([latex_code])


# usage example
A = np.array([[1,  1, -1, 1],
              [1,  3,  0, 2],
              [3, -1,  5, 1]])


print(augmented_matrix_to_latex(A, [('subtract', 3, 1, 3)]))

# output:

