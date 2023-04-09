import os
import numpy as np
import copy
import sys

def load_sudoku(puzzle_path):
    ''' Load the sudoku from the given path; it returns the sudoku as a list of lists
        input: puzzle_path: path to the puzzle
        output: ret: the sudoku as a list of lists where -1 represents an empty cell
        and 0-8 represents the value in the cell corresponding to the numbers 1-9
    '''
    ret = []
    with open(puzzle_path, 'r') as sudoku_f:
        for line in sudoku_f:
            line = line.rstrip()
            cur = line.split(" ")
            cur = [ord(x) - ord('1') if x.isdigit() else -1 for x in cur]
            ret.append(cur)
    return ret


def isSolved(sudoku, **kwargs):
    '''' Check if the sudoku is solved
        input: sudoku: the sudoku to be solved
               kwargs: other keyword arguments
        output: True if solved, False otherwise
    '''
    solved = True
    #If there are any unassigned variables, return false
    for row in sudoku:
        if -1 in row:
            solved = False
            return solved

    #If row elements are not unque, return false    
    for row in sudoku:
        if len(set(row)) != 9:
            return False

    #If column elements are not unique, return false    
    for i in range(0,9):
        col = []
        for j in range(0,9):
            col.append(sudoku[j][i])
        if len(set(col)) != 9:
            return False

    #If box elements are not unique, return false
    for m in range(0,3):
        for n in range (0,3):
            box = []
            for i in range(0,3):
                for j in range(0,3):
                    box.append(sudoku[i+(m*3)][j+(n*3)])

            if len(set(box)) != 9:
                return False

    return solved

'''
Function to update the domain value of variable [x,y]
where x is the row number and y is the column number
'''
def update_domain_values(sudoku, domain, x, y):
    domain[x][y] = []
    domain[x][y] = get_domain_values(sudoku,x,y)


def undo_changes_for_position(sudoku, x, y, val, **kwargs):
    ''' Undo the changes made for the given position
        input: sudoku: the sudoku to be solved
               x: row number
               y: column number
               val: value to be checked
               kwargs: other keyword arguments
        output: None
    '''

    domain = kwargs["domain"]
    fixed = kwargs["fixed"]
    
    fixed[x][y] = False
    sudoku[x][y] = -1
    update_domain_values(sudoku,domain,x,y)
    
    #row append
    column_number = 0
    for domain_element in domain[x]:
        #Check if the element val is already in domain. If yes, no need to add this
        #element again. Also see whether the variable is unassigned. We only have to
        #modify the domains of variables that are unassigned

        if val not in domain_element and is_element_fixed(fixed,x,column_number)==False:
            update_domain_values(sudoku, domain, x, column_number)
        
        column_number=column_number+1

    #column append
    row_number=0
    for domain_row in domain:
        if val not in domain_row[y] and is_element_fixed(fixed,row_number,y)==False:
            update_domain_values(sudoku, domain, row_number, y)

        row_number = row_number+1

    startRow, startCol = get_start_box_variable(x,y)

    for i in range(0,3):
        for j in range(0,3):
            if val not in domain[startRow+i][startCol+j] and is_element_fixed(fixed,startRow+i,startCol+j)==False:
                update_domain_values(sudoku, domain, startRow+i, startCol+j)

    return

def is_element_fixed(fixed,x,y):
    return fixed[x][y]

def update_changes_for_position(sudoku, x, y, val, **kwargs):
    ''' Update the changes for the given position
        input: sudoku: the sudoku to be solved
               x: row number
               y: column number
               val: value to be checked
               kwargs: other keyword arguments
        output: None
    '''
    domain = kwargs["domain"]
    fixed = kwargs["fixed"]
    
    sudoku[x][y] = val
    fixed[x][y] = True

    domain[x][y] = []
    domain[x][y].append(val)

    #Remove the val form all the variables in the row
    column_number = 0
    for domain_element in domain[x]:
        if val in domain_element and is_element_fixed(fixed,x,column_number)==False:
            domain_element.remove(val)
        column_number = column_number+1

    #Remove the val from all the variables in the column
    row_number = 0
    for domain_row in domain:
        if val in domain_row[y] and is_element_fixed(fixed,row_number,y)==False:
            domain_row[y].remove(val)
        row_number = row_number+1

    startRow, startCol = get_start_box_variable(x,y)

    #Remove the val from all the variables in the box
    for i in range(0,3):
        for j in range(0,3):
            if val in domain[startRow+i][startCol+j] and is_element_fixed(fixed,startRow+i,startCol+j)==False:
                domain[startRow+i][startCol+j].remove(val)
    return


def isPossible(sudoku, x, y, val, **kwargs):
    ''' Check if the value(val) is possible at the given position (x, y)
        input: sudoku: the sudoku to be solved
               x: row number
               y: column number
               val: value to be checked
               kwargs: other keyword arguments
        output: True if possible, False otherwise
    '''
    domain = kwargs["domain"]
    fixed = kwargs["fixed"]

    #If element already fixed,
    if fixed[x][y]:
        return False
    else:
        if val in domain[x][y]:
            return True
        else:
            return False


def get_mrv_position(sudoku, **kwargs):
    ''' Get the position with minimum remaining values
        input: sudoku: the sudoku to be solved
               kwargs: other keyword arguments'
        output: x: row number
                y: column number'''
    
    #since tie breaking in MRV is the degree heuristic 
    #and since all the variables in sudoku have the same degree
    #we tiebreak on first come first serve basis
    domain = kwargs["domain"]
    fixed = kwargs["fixed"]
    min_domain = 10
    mrv_row_number=10
    mrv_col_number=10

    for i in range(0,9):
        for j in range(0,9):
            if not fixed[i][j]:
                if len(domain[i][j]) < min_domain:
                    mrv_row_number = i
                    mrv_col_number = j
                    min_domain = len(domain[i][j])
                
    return mrv_row_number,mrv_col_number



def undo_waterfall_changes(sudoku, changes, **kwargs):
    ''' Undo the changes made by the waterfalls
        input: sudoku: the sudoku to be solved
               changes: list of changes made by the waterfalls previously
               kwargs: other keyword arguments
        output: None

    '''
    #We need to add all the domain elements that were removed back to the original domain list
    domain = kwargs["domain"]

    for element in changes:
        variable = element[0]
        value_to_be_added = element[1]

        x,y = get_variables_in_ac3(variable)
        if value_to_be_added not in domain[x][y]:
            domain[x][y].append(value_to_be_added)
    

def apply_waterfall_methods(sudoku, list_of_waterfalls, **kwargs):
    ''' Apply the waterfall methods to the sudoku
        input: sudoku: the sudoku to be solved
               list_of_waterfalls: list of waterfall methods
               kwargs: other keyword arguments
        output: isPoss: True if the sudoku is solved, False otherwise
                all_changes: list of changes made by the waterfalls'''
    all_changes = []
    #Keep applying the waterfalls until no change is made
    while True:
        #Flag to check if any change is made by the waterfalls
        any_chage = False
        for waterfall in list_of_waterfalls:
            isPoss, changes = waterfall(sudoku, **kwargs)
            all_changes += changes
            # If any change is made, then set the flag to True
            if len(changes) > 0:
                any_chage = True
            # If the sudoku is not possible fill up, then return False and the changes made to be undone
            if not isPoss:
                return False, all_changes
        # If no change is made by the waterfalls at current iteration, then break
        if not any_chage:
            break
    return True, all_changes


def get_next_position_to_fill(sudoku, x, y, mrv_on, **kwargs):
    ''' Get the next position to fill durin the backtracking
        input: sudoku: the sudoku to be solved
               x: row number
               y: column number
               mrv_on: True if mrv is on, False otherwise
               kwargs: other keyword arguments
        output: nx: next row number
                ny: next column number'''

    if mrv_on:
        x,y = get_mrv_position(sudoku,**kwargs)
        return x,y
    else:
        if x==-1 and y==-1:
            for i in range(0,9):
                for j in range(0,9):
                    if sudoku[i][j] == -1:
                        return i,j
        else:
            if y < 8:
                for j in range(y+1,9):
                    if sudoku[x][j]== -1:
                        return x,j
            
            for i in range(x+1,9):
                for j in range(0,9):
                    if sudoku[i][j] == -1:
                        return i,j
                
        return 10,10

def solve_sudoku(sudoku, x, y, mrv_on, list_of_waterfalls, **kwargs):
    '''' Solve the sudoku using the given waterfall methods with/without mrv
        input: sudoku: the sudoku to be solved
               x: row number of the current position
               y: column number the current position
               mrv_on: True if mrv is on, False otherwise
               list_of_waterfalls: list of waterfalls to be applied
               kwargs: other keyword arguments
               output:  True if solved, False otherwise
                        sudoku: the solved sudoku
                        guess: number of guesses made'''
    
    #Feel free to change the function as you need, for example, you can change the keyword arguments in the function calls below
    #First you need to check whether the sudoku is solved or not
    domain = kwargs["domain"]
    fixed = kwargs["fixed"]
    if isSolved(sudoku):
        return True, sudoku, 0
    #Apply the waterfalls; change the kwargs with your own
    isPoss, changes = apply_waterfall_methods(sudoku, list_of_waterfalls, **kwargs)

    # If the sudoku is not possible, undo the changes and return False
    if not isPoss:
        undo_waterfall_changes(sudoku, changes, **kwargs)
        return False, sudoku, 0
    #After waterfalls are applied, now you need to check if the current position is already filled or not; if it is filled, 
    #then you need to get the next position to fill

    if sudoku[x][y] != -1:
        nx, ny = get_next_position_to_fill(sudoku, x, y, mrv_on, **kwargs)

        if nx !=-1:
            solved, sudoku, guess = solve_sudoku(sudoku, nx, ny, mrv_on, list_of_waterfalls, **kwargs)

        if isSolved(sudoku):
            return True, sudoku, guess
        else:
            #Undo the changes made by the already applied waterfalls

            undo_waterfall_changes(sudoku, changes, **kwargs)
            
            return False, sudoku, guess
    


    no_cur_guess = 0
    #Check how many guesses are possible for the current position
    for i in range(9):
        if isPossible(sudoku, x, y, i, **kwargs):
            no_cur_guess += 1
        
    if no_cur_guess == 0:
        return False, sudoku, 0

    for i in range(9):
        #Check if the value is possible at the current position
        if isPossible(sudoku, x, y, i, **kwargs):
            #If the value is possible, then update the changes for the current position
            update_changes_for_position(sudoku, x, y, i, **kwargs)
            #Get the next position to fill
            nx, ny = get_next_position_to_fill(sudoku, x, y, mrv_on, **kwargs)
            #Solve the sudoku for the next position
            if nx!=10:
                solved, sudoku, guesses = solve_sudoku(sudoku, nx, ny, mrv_on, list_of_waterfalls, **kwargs)
                no_cur_guess += guesses

            #If the sudoku is solved, then return True, else undo the changes for the current position
            if isSolved(sudoku):
                return True, sudoku, no_cur_guess - 1
            else:
                undo_changes_for_position(sudoku, x, y, i, **kwargs)
    
    #If the sudoku cannot solved at current partially filled state, then undo the changes made by the waterfalls and return False
    undo_waterfall_changes(sudoku, changes, **kwargs)
    return False, sudoku, no_cur_guess - 1

'''
Helper function to get the variable [x,y] in the form xy
where x is the row number and y is the column number
'''
def get_variable_name(x,y):
    return (x*10) + y

'''
Get the variable position from xy
Output:x,y where x is the row number and
       y is the column number
'''
def get_variables_in_ac3(val):
    x=int(val/10)
    y=int(val%10)
    return x,y

'''
Get the starting point for the 3*3 box for a
variable x,y where x is the row number and 
y is the column number
'''
def get_start_box_variable(x,y):
    startRow = int(x/3)
    startCol = int(y/3)
    return startRow*3, startCol*3

'''
Helper function to create an arc 
first_variable--->second_variable
'''
def create_arc(first_variable, second_variable):
    arc = []
    arc.append(first_variable)
    arc.append(second_variable)
    return arc

'''
Get all the arcs for the first_variable
We get arcs in the form first_variable--->dependent_variable if reverse is false
If reverse is true, we get dependent_variable--->first_variable
'''
def add_dependent_variables(first_variable,arc3_queue, reverse):
    x,y = get_variables_in_ac3(first_variable)
    for row_number in range(0,9):
        if row_number != x:
            second_variable = (row_number*10) + y
            if reverse:
                arc = create_arc(second_variable, first_variable)
            else:
                arc = create_arc(first_variable, second_variable)
            if arc not in arc3_queue:
                arc3_queue.append(arc)

    for col_number in range(0,9):
        if col_number != y:
            second_variable = (x*10) + col_number
            if reverse:
                arc = create_arc(second_variable, first_variable)
            else:
                arc = create_arc(first_variable, second_variable)
            if arc not in arc3_queue:
                arc3_queue.append(arc)

    startRow, startCol = get_start_box_variable(x,y)

    for i in range(0,3):
        for j in range(0,3):
            if startRow+i != x and startCol+j != y:
                second_variable = ((startRow+i)*10)+(startCol+j)
                if reverse:
                    arc = create_arc(second_variable, first_variable)
                else:
                    arc = create_arc(first_variable, second_variable)
                if arc not in arc3_queue:
                    arc3_queue.append(arc)

    return arc3_queue

'''
Populate the initial constarints for AC3
'''
def populate_initial_constraints(arc3_queue):
    for x in range(0,9):
        for y in range(0,9):
            first_variable = (x*10) + y
            add_dependent_variables(first_variable,arc3_queue, False)

    return arc3_queue

'''
Revise function of AC-3
'''
def revise(sudoku, domain, arc, changes):
    revised = False
    first_variable = arc[0]
    second_variable = arc[1]
    first_x,first_y = get_variables_in_ac3(first_variable)
    second_x, second_y = get_variables_in_ac3(second_variable)

    first_var_domain = domain[first_x][first_y]
    second_var_domain = domain[second_x][second_y]

    for value in first_var_domain:
        delete_value = True
        for value_in_second_domain in second_var_domain:
            if value != value_in_second_domain:
                #A different value is found in second domain. So don't need to delete the value
                delete_value = False
                break
        #Delete the value in the first domain 
        if delete_value:
            revised = True

            first_var_domain.remove(value)
            #Need to save this in the changes list
            changed_node = []
            changed_node.append(first_variable)
            changed_node.append(value)
            if changed_node not in changes:
                changes.append(changed_node)
            
    return revised


def ac3_waterfall(sudoku, **kwargs):
    '''The ac3 waterfall method to apply
    input:  sudoku: the sudoku to apply AC-3 method on'
            kwargs: the kwargs to be passed to the isPossible function
    output: isPoss: whether the sudoku is still possible to solve (i.e. not inconsistent))
            changes: the changes made to the sudoku'''
    #Structure of changes is [[variable, deleted_domain_value],....]
    changes = []

    #Write your code here
    domain = kwargs["domain"]
    arc3_queue = []
    arc3_queue = populate_initial_constraints(arc3_queue)

    while len(arc3_queue) > 0:
        arc = arc3_queue[0]
        first_variable = arc[0]
        second_variable = arc[1]
        first_x,first_y = get_variables_in_ac3(first_variable)
        second_x, second_y = get_variables_in_ac3(second_variable)

        arc3_queue.remove(arc)

        if (revise(sudoku, domain,  arc, changes)):
            if len(domain[first_x][first_y])==0:
                return False, changes
            
            #add neighbors of first_variables to the queue as the domain of first_variable is changed
            add_dependent_variables(first_variable,arc3_queue,True)
    return True, changes

'''
Returns the list of domains for all dependent variables for x,y
'''
def get_domain_of_all_rel_variables(sudoku, domain, x,y):
    domain_of_rel_variables = []
    #Get all domain values in row
    column_number = 0
    for domain_element in domain[x]:
        #Skip the element under consideration
        if column_number != y:
            #Iterate over all values and if not present, add it
            for values in domain_element:
                if values not in domain_of_rel_variables:
                    domain_of_rel_variables.append(values)
        column_number = column_number+1

    #Get all domain values in column
    row_number = 0
    for domain_row in domain:
        #Skip the elemnet under consideration
        if row_number != x:
            #Iterate over all values and if not present, add it
            for values in domain_row[y]:
                if values not in domain_of_rel_variables:
                    domain_of_rel_variables.append(values)
        row_number = row_number+1

    #Get all domain values in box
    startRow, startCol = get_start_box_variable(x,y)

    for i in range(0,3):
        for j in range(0,3):
            #Skip element under consideration
            if startRow+i != x and startRow+j != y:
                ind_domain = domain[startRow+i][startCol+j]
                #Iterate over all the values in domain and if not present in main
                #list, add it
                for values in ind_domain:
                    if values not in domain_of_rel_variables:
                        domain_of_rel_variables.append(values)


    return domain_of_rel_variables

#Implementing the hidden singles inference rule, wherein if an elemnt has a value
#in it's domain and that value is not present in any other domain of it's related
#variable, then that is the value of that variable
def waterfall1(sudoku, **kwargs):
    '''The first waterfall method to apply
    input:  sudoku: the sudoku to apply the waterfall method on
            kwargs: the kwargs to be passed to the isPossible function
    output: isPoss: whether the sudoku is still possible to solve (i.e. not inconsistent))
            changes: the changes made to the sudoku'''

    changes = []
    domain = kwargs["domain"]
    for x in range(0,9):
        for y in range(0,9):
            domain_of_all_related_variable = get_domain_of_all_rel_variables(sudoku,domain,x,y)

            hidden_single = -1
            #Iterate over all the values in the domain for variable under consideration
            #If a value is found in this variable such that all the neighboring variables
            #donot have this value, then this is the hidden_single
            #Only possible to find a single such value for any variable in sudoku
            count = 0
            for value in domain[x][y]:
                if value not in domain_of_all_related_variable:
                    hidden_single = value
                    count = count+1
            
            #This should not be possible. Thus, this is a non-correct state
            if count > 1:
                return False, changes
            
            #If hidden single is found, then we make this as the only value in the variable's domain
            #We delete all the remaining values from this variable's domain
            if hidden_single != -1:
                for value in domain[x][y]:
                    if value != hidden_single:
                        changed_node = []
                        changed_node.append(get_variable_name(x,y))
                        changed_node.append(value)
                        if changed_node not in changes:
                            changes.append(changed_node)

                domain[x][y] = []
                domain[x][y].append(hidden_single)

    #Always return isPoss as True as we know for sure that the inference rule used here
    #would have a possible solution. This just reduces the domain of the hidden_single variable
    #to 1
    return True, changes

def waterfall2(sudoku, **kwargs):
    '''The second waterfall method to apply
    input:  sudoku: the sudoku to apply the waterfall method on
            kwargs: the kwargs to be passed to the isPossible function
    output: isPoss: whether the sudoku is still possible to solve (i.e. not inconsistent))
            changes: the changes made to the sudoku'''

    changes = []
    #Write your code here
    return False, changes



def get_all_waterfall_methods():
    '''Get all the waterfall methods as list.'''
    pass

'''
Get the domain values for the given variable x,y
'''
def get_domain_values(sudoku,x,y):
    possible_domain = [0,1,2,3,4,5,6,7,8]

    for val in sudoku[x]:
        if val in possible_domain:
            possible_domain.remove(val)

    for row in sudoku:
        if row[y] in possible_domain:
            possible_domain.remove(row[y])

    startRow, startCol = get_start_box_variable(x,y)

    for i in range(0,3):
        for j in range(0,3):
            if sudoku[startRow+i][startCol+j] in possible_domain:
                possible_domain.remove(sudoku[startRow+i][startCol+j])

    return possible_domain

def get_initial_kwargs(sudoku, mrv_on, **kwargs):
    '''Get the initial kwargs for the solve_sudoku function.
    input:  sudoku: the sudoku to solve
            mrv_on: whether to use the mrv heuristic
            kwargs: other keyword arguments
    output: kwargs: the kwargs to be passed to the solve_sudoku function
    '''
    initial_domain = []
    initial_fixed = []
    initial_saved = {}

    #do something
    for i in range(9):
        row_domain = []
        row_fixed = []
        initial_domain.append(row_domain)
        initial_fixed.append(row_fixed)
        for j in range(9):
            if sudoku[i][j] != -1:
                row_fixed.append(True)
                domain_element = []
                domain_element.append(sudoku[i][j])
            else:
                row_fixed.append(False)
                domain_element = get_domain_values(sudoku,i,j)

            row_domain.append(domain_element)

    kwargs = {"domain":initial_domain, "fixed":initial_fixed, "saved_domains":initial_saved}
    return kwargs

def solve_plain_backtracking(original_sudoku):
    '''Solve the sudoku using plain backtracking.'''
    sudoku = copy.deepcopy(original_sudoku)
    kwargs = get_initial_kwargs(sudoku, False)
    ini_x, ini_y = 0, 0
    return solve_sudoku(sudoku, ini_x, ini_y, False, [], **kwargs)

def solve_with_mrv(original_sudoku):
    '''Solve the sudoku using mrv heuristic.'''
    sudoku = copy.deepcopy(original_sudoku)
    kwargs = get_initial_kwargs(sudoku, True)
    ini_x, ini_y = get_next_position_to_fill(sudoku, -1, -1, True, **kwargs)
    return solve_sudoku(sudoku, ini_x, ini_y, True, [], **kwargs)

def solve_with_ac3(original_sudoku):
    '''Solve the sudoku using mrv heuristic and ac3 waterfall method.'''
    sudoku = copy.deepcopy(original_sudoku)
    all_waterfalls = [ac3_waterfall]
    kwargs = get_initial_kwargs(sudoku, True)
    ini_x, ini_y = get_next_position_to_fill(sudoku, -1, -1, True, **kwargs)
    return solve_sudoku(sudoku, ini_x, ini_y, True, all_waterfalls, **kwargs)

def solve_with_addition_of_waterfall1(original_sudoku):
    '''Solve the sudoku using mrv heuristic and waterfall1 waterfall method besides ac3.'''
    sudoku = copy.deepcopy(original_sudoku)
    all_waterfalls = [ac3_waterfall, waterfall1]
    kwargs = get_initial_kwargs(sudoku, True)
    ini_x, ini_y = get_next_position_to_fill(sudoku, -1, -1, True, **kwargs)
    return solve_sudoku(sudoku, ini_x, ini_y, True, all_waterfalls, **kwargs)

def solve_with_addition_of_waterfall2(original_sudoku):
    '''Solve the sudoku using mrv heuristic and waterfall2 waterfall method besides ac3 and waterfall1.'''
    sudoku = copy.deepcopy(original_sudoku)
    all_waterfalls = [ac3_waterfall, waterfall1, waterfall2]
    kwargs = get_initial_kwargs(sudoku, True)
    ini_x, ini_y = get_next_position_to_fill(sudoku, -1, -1, True, **kwargs)
    return solve_sudoku(sudoku, ini_x, ini_y, True, all_waterfalls, **kwargs)



def solve_one_puzzle(puzzle_path):

    sudoku = load_sudoku(puzzle_path)
    waterfall2_guesses=0

    solved, solved_sudoku, backtracking_guesses = solve_plain_backtracking(sudoku)
    assert solved

    solved, solved_sudoku, mrv_guesses = solve_with_mrv(sudoku)   
    assert solved

    solved, solved_sudoku, ac3_guesses = solve_with_ac3(sudoku)
    assert solved

    solved, solved_sudoku, waterfall1_guesses = solve_with_addition_of_waterfall1(sudoku)
    assert solved
    '''
    solved, solved_sudoku, waterfall2_guesses = solve_with_addition_of_waterfall2(sudoku)
    assert solved
    #Add more waterfall methods here if you want need to and return the number of guesses for each method
    '''
    return (backtracking_guesses, mrv_guesses, ac3_guesses, waterfall1_guesses, waterfall2_guesses)

def solve_all_sudoku():
    puzzles_folder = "puzzles"
    puzzles = os.listdir(puzzles_folder)
    puzzles.sort()
    for puzzle_file in puzzles:
        puzzle_path = os.path.join(puzzles_folder, puzzle_file)

        backtracking_guesses, mrv_guesses, ac3_guesses, waterfall1_guesses, waterfall2_guesses = solve_one_puzzle(puzzle_path)
        print("Puzzle: ", puzzle_file)
        print("backtracking guesses: ", backtracking_guesses)
        print("mrv guesses: ", mrv_guesses)
        print( "ac3 guesses: ", ac3_guesses)
        print("with waterfall1 guesses: ", waterfall1_guesses)
        #print("with waterfall2 guesses: ", waterfall2_guesses)


if __name__ == '__main__':
    sys.setrecursionlimit(20000)
    solve_all_sudoku()