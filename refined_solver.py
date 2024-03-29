#!/usr/bin/env python
# coding: utf-8

# 
# # Hyper Parameters
# 
# 1) T (temperature) : The temperature T provides a means to control the balance between the time spent
#  visiting unsatisfying assignments and the ability to move between separated regions of solutions.
#   When the temperature is high, the distribution is smooth and we move easily between solution regions,
#    but the total probability of non-solution states can be large compared to the total probability of solutions.
#  Conversely, a low temperature biases the distribution toward solutions at the cost of effectively disconnecting solution regions
# 
# - in our application(no need to have a good target distribution since we generate only ONE SAMPLE per RUN) we need low T as possible
# 
# -------------------------------------------------------------
# 
# 2) pls : probability of taking local search move,  (1-pls) -> metropolis move
# Although our local-search moves are based on the same distributions as our MetropolisHastings moves, they do not use the acceptance rule,
#  so they distort the stationary distribution away from the target distribution.
#  

# This packages will be needed 

import numpy as np
import random
import copy
import math


# This global constants will be needed 


TEMPERATURE=1
PLS0=0
pls=0
SEED=5
random.seed(SEED)
np.random.seed(SEED)


# These constants represent the maximum input sizes , for example here the number of clauses is 7 , you can input only 3 and zeros for the other 4 clauses.


NUM_OF_BOOL_VARIABLES=1  # x0,[x1,x2,...] NUM_OF_BOOL_VARIABLES in all formula  
NUM_OF_INT_VARIABLES=3   # y0+y1+y2+bias<=0  in all formula and in the one literal and in all formula 
NUM_OF_BOOL_LITERALS=1   # [0(exist)/1(not exist)]x0  NUM_OF_BOOL_LITERALS in one clause
NUM_OF_INT_LITERALS=2    # y0+y1+y2+bias<=0 or y0+y1+y2+bias<=0 or y0+y1+y2+bias<=0  NUM_OF_INT_LITERALS in one clause
NUM_OF_CLAUSES=7         # clause0 and clause1 and clause2  NUM_OF_CLAUSES in formula


# These are derived constants , the number of rows means how much rows that a [literal or clause] may occupy in the formula (array or buffer).  


INT_LITERAL_NUM_OF_ROWS=NUM_OF_INT_VARIABLES+1
BOOL_LITERAL_NUM_OF_ROWS=2
CLAUSE_NUM_OF_ROWS=NUM_OF_BOOL_LITERALS*BOOL_LITERAL_NUM_OF_ROWS+NUM_OF_INT_LITERALS*INT_LITERAL_NUM_OF_ROWS
FORMULA_NUM_OF_ROWS=CLAUSE_NUM_OF_ROWS*NUM_OF_CLAUSES


# # NOTES
# - each boolean literal has tow rows in formula list one for exist or not exist and second for x0 or ~x0
# - always NUM_OF_BOOL_VARIABLES=NUM_OF_BOOL_LITERALS
# - No variable names

# The following is input hardcoding instead of reading the formula (array or buffer)from a text file  , and also for the size of int variables .
# <img src="formula.PNG" style="width:250;height:300px;">


formula=[]
#clause0
formula.append(0) # [not exist]~x0
formula.append(0)
formula.append(-1) # -y0+2<=0
formula.append(0)
formula.append(0)
formula.append(2)
formula.append(0) # not exist int literal
formula.append(0)
formula.append(0)
formula.append(0)
#clause1
formula.append(0) # [not exist]~x0
formula.append(0)
formula.append(1) # y0-16<=0
formula.append(0)
formula.append(0)
formula.append(-16)
formula.append(0) # not exist int literal
formula.append(0)
formula.append(0)
formula.append(0)
#clause2
formula.append(0) # [not exist]~x0
formula.append(0)
formula.append(0) # -y1<=0
formula.append(-1)
formula.append(0)
formula.append(0)
formula.append(0) # not exist int literal
formula.append(0)
formula.append(0)
formula.append(0)
#clause3
formula.append(0) # [not exist]~x0
formula.append(0)
formula.append(0) # -y2<=0
formula.append(0)
formula.append(-1)
formula.append(0)
formula.append(0) # not exist int literal
formula.append(0)
formula.append(0)
formula.append(0)
#clause4
formula.append(1) # [ exist]x0
formula.append(1)
formula.append(1) # y0+y1-12<=0
formula.append(1)
formula.append(0)
formula.append(-12)
formula.append(0) # not exist int literal
formula.append(0)
formula.append(0)
formula.append(0)
#clause5
formula.append(1) # [exist]~x0
formula.append(0)
formula.append(1) # y0+y1-16<=0
formula.append(1)
formula.append(0)
formula.append(-16)
formula.append(-1) # -y0+y1<=0
formula.append(1)
formula.append(0)
formula.append(0)
#clause6
formula.append(1) # [exist]~x0
formula.append(0)
formula.append(1) # y0-y1-18<=0
formula.append(-1)
formula.append(0)
formula.append(-18)
formula.append(0) # y1+2y2-20<=0
formula.append(1)
formula.append(2)
formula.append(-20)
##########################################################################################
bit_width_for_int_variables=[]
bit_width_for_int_variables.append(8)
bit_width_for_int_variables.append(8)
bit_width_for_int_variables.append(8)


# These two global arrays represent the current assignment for all bool and int variables


current_values_int=[]
current_values_bool=[]


# # Modules(functions) 
# - global variables are usually inputs for all functions , so I don't write them in parameter list of each function

# # 1) compute_pls


def compute_pls(iteration_number):
    pls = PLS0 * math.exp(1-iteration_number)
    if (pls>1):
        pls = 1
    elif (pls <0):
        pls = 0
        
    pls = pls


# # 2) make_random_assignment_int
# - assign random values to all int variables


def make_random_assignment_int():
    for i in range(NUM_OF_INT_VARIABLES):
         maximum=math.pow(2,bit_width_for_int_variables[i]-1)-1
         minimum=-math.pow(2,bit_width_for_int_variables[i]-1)-1
         current_values_int.append(random.randint(minimum,maximum))


# # 3) make_random_assignment_bool
# - assign random values to all bool variables


def make_random_assignment_bool():
    for i in range(NUM_OF_BOOL_VARIABLES):
        current_values_bool.append(random.randint(0,1))


# # 4) check_int_literal
# - check satisfiability of a specific int literal under the global current assignment


def check_int_literal(clause_num,int_literal_num):
    
    clause=[]
    first_c=clause_num *CLAUSE_NUM_OF_ROWS
    last_c=first_c+CLAUSE_NUM_OF_ROWS
    clause=formula[first_c:last_c]
    
    int_literal=[]
    first=(int_literal_num*INT_LITERAL_NUM_OF_ROWS)+BOOL_LITERAL_NUM_OF_ROWS
    last=first+INT_LITERAL_NUM_OF_ROWS
    int_literal=clause[first:last]
    
    #if not exist
    exist=0
    for i in range(INT_LITERAL_NUM_OF_ROWS):
        if int_literal[i]!=0:
            exist=1
    if exist==0:
        return -1
    
    count = 0
    for j in range(NUM_OF_INT_VARIABLES):
        count += int_literal[j] * current_values_int[j]
    count += int_literal[-1] #bias
    if count <= 0:
        return True

    return False


# # 5) check_bool_literal
# - check satisfiability of a specific bool literal under the global current assignment


def check_bool_literal(clause_num,bool_literal_num):
    clause=[]
    first_c=clause_num *CLAUSE_NUM_OF_ROWS
    last_c=first_c+CLAUSE_NUM_OF_ROWS
    clause=formula[first_c:last_c]
    bool_literal=[]
    first=bool_literal_num*BOOL_LITERAL_NUM_OF_ROWS
    last=first+BOOL_LITERAL_NUM_OF_ROWS
    bool_literal=clause[first:last]
    
    #if not exist
    if bool_literal[0]==0 :#not exist bool literal
        return -1
    
    elif current_values_bool[bool_literal_num]==bool_literal[1]:
        return True
    else:
        return False 


# # 6) check_clause


def check_clause(clause_num):#from 0 to NUM_OF_CLAUSES-1
    clause=[]
    first_c=clause_num *CLAUSE_NUM_OF_ROWS
    last_c=first_c+CLAUSE_NUM_OF_ROWS
    clause=formula[first_c:last_c]
    
    #if not exist
    exist=0
    for i in range(CLAUSE_NUM_OF_ROWS):
        if clause[i]!=0:
            exist=1
    if exist==0:
        return -1
    
    for j in range(NUM_OF_BOOL_LITERALS):
        if check_bool_literal(clause_num,j)==True :
            return True
    for k in range(NUM_OF_INT_LITERALS):
        if check_int_literal(clause_num,k)==True :
            return True
    return False


# # 7) check_formula


def check_formula():
    for i in range(NUM_OF_CLAUSES):
        if check_clause(i)==False:
            return False
    return True


# # 8) find_number_of_unsatisfied_clauses


def find_number_of_unsatisfied_clauses():
    c=0
    for i in range(NUM_OF_CLAUSES):
        if check_clause(i)==False:
            c+=1
    return c


# # 9) reduce_literal
# - substitute for a literal to get a selected variable alone . (y<=c) or (y>=c)


def reduce_literal(clause_num,int_literal_num,index_variable_to_be_unchanged):# from 0 to NUM_OF_INT_VARIABLES-1
    clause=[]
    first_c=clause_num *CLAUSE_NUM_OF_ROWS
    last_c=first_c+CLAUSE_NUM_OF_ROWS
    clause=formula[first_c:last_c]
    
    int_literal=[]
    first=(int_literal_num*INT_LITERAL_NUM_OF_ROWS)+BOOL_LITERAL_NUM_OF_ROWS
    last=first+INT_LITERAL_NUM_OF_ROWS
    int_literal=clause[first:last]

    reduced_int_literal=[]
    reduced_int_literal=int_literal
    
    # this variable is not found in that int literal
    if reduced_int_literal[index_variable_to_be_unchanged] == 0:
            return False

    new_bias = 0
    bias_updating=False
    for i in range(NUM_OF_INT_VARIABLES):
        if i != index_variable_to_be_unchanged:
            if int_literal[i]!=0:
                bias_updating=True 
            new_bias += current_values_int[i] * int_literal[i]
            reduced_int_literal[i] = 0

    #updating the bias
    if bias_updating==True:
        reduced_int_literal[-1] =int_literal[-1] +new_bias
    
    # +ve value coeff                                                                     
    if(reduced_int_literal[index_variable_to_be_unchanged] > 0): 
        reduced_int_literal[-1] /= int_literal[index_variable_to_be_unchanged]
        reduced_int_literal[index_variable_to_be_unchanged] = 1
    
    # -ve value coeff
    else: 
        reduced_int_literal[-1] /= (-1 * int_literal[index_variable_to_be_unchanged])
        reduced_int_literal[index_variable_to_be_unchanged] = -1


    #should be something like the form of y1 + 10 <= 0 or -1 y1 +5 <= 0
    return reduced_int_literal


# # 10) get_active_clauses(active formula)
# - For an integer variable yi, we construct a proposal distribution from the ranges of values
# that satisfy individual relations. Not all of the relations that refer to yi necessarily contribute to the distribution for the current move; some of them do not constrain yi under the current assignment (x, y) because their clauses are already satisfied by other literals that do not depend on yi. We call the relations that do constrain yi the active relations. To identify them, we substitute the current values of (x, y \ yi) into all clauses in the formula ϕ and remove falsified literals and satisfied clauses. We call the resulting substituted clauses the active clauses.[1]


def get_active_clauses(index_variable_to_be_unchanged): # return active formula
    
    active_formula=[0]*FORMULA_NUM_OF_ROWS
    for i in range(NUM_OF_CLAUSES):
        skip=0
        active_clause=[0]*CLAUSE_NUM_OF_ROWS

        for j in range(NUM_OF_BOOL_LITERALS):
            if check_bool_literal(i,j)==True:
                skip=1 # the clause is satisfied
                
        if skip==0:# the clause is not satisfied
            for k in range(NUM_OF_INT_LITERALS):
                reduced_int_literal=reduce_literal(i,k,index_variable_to_be_unchanged)
                if reduced_int_literal==False: # this variable is not in that int literal
                    if check_int_literal(i,k)==True:# Skip the whole clause
                        skip=1
        if skip==0: # the clause is not satisfied 
            for k in range(NUM_OF_INT_LITERALS):
                reduced_int_literal=reduce_literal(i,k,index_variable_to_be_unchanged)
                if reduced_int_literal!=False: # this variable is in that int literal
                    first=(k*INT_LITERAL_NUM_OF_ROWS)+BOOL_LITERAL_NUM_OF_ROWS
                    last=first+INT_LITERAL_NUM_OF_ROWS
                    active_clause[first:last]=reduced_int_literal
        

        first_c=i *CLAUSE_NUM_OF_ROWS
        last_c=first_c+CLAUSE_NUM_OF_ROWS
        active_formula[first_c:last_c]= active_clause
    return active_formula


# The example in Figure 3.2 illustrates how the active clauses are obtained by substitution
# and simplification of ϕ.
# <img src="active clauses.PNG" style="width:250;height:300px;">
# 
# 


#test active clauses 
current_values_int=[5,11,4] # the current value for y1 doesn't matter
current_values_bool=[1]
print(get_active_clauses(0)) # y1 is the 0 variable (first)


# # Getting the proposal distribution
# - We construct the proposal distribution q(yi|x, y \ yi) by combining indicator functions
# for the active relations. Like the active clauses, the combination of indicators has a two-level structure: For each clause C, we take the pointwise max of the indicators for relations in C to get an indicator for the clause as a whole. Then we conjoin the clause indicators to create a distribution. [1]

# The meaning of ( uniform ,exp_up ,exp_down ) segments(intervals)
# <img src="Capture.PNG" style="width:250;height:300px;">


#encoding
UNIFORM=3
EXP_UP=2
EXP_DOWN=1
#########


# The interval(segment) is defined as an array of 3 elements ( from , to , type ) ,
# type is ( uniform(3) ,exp_up(2) or exp_down(1) ) .
# The indicator will be explained later.


INTERVAL_NUM_OF_ROWS=3 # range and type (uniform or exp)
INDICATOR_NUM_OF_ROWS=2*INTERVAL_NUM_OF_ROWS  #indicator for one reduced literal has two intervals
NUM_OF_INTERVALS_IN_CLAUSE_INDICATOR=math.pow(2,NUM_OF_INT_LITERALS)
NUM_OF_INTERVALS_IN_FORMULA_INDICATOR=math.pow(NUM_OF_INTERVALS_IN_CLAUSE_INDICATOR,NUM_OF_CLAUSES)
CLAUSE_INDICATOR_NUM_OF_ROWS=NUM_OF_INTERVALS_IN_CLAUSE_INDICATOR*INTERVAL_NUM_OF_ROWS
FORMULA_INDICATOR_NUM_OF_ROWS=NUM_OF_INTERVALS_IN_FORMULA_INDICATOR*INTERVAL_NUM_OF_ROWS


# # Indicator & distributions class


class Indicator:
    _from = int
    _to = int
    _type = int

    def __init__(self,indi):
        self._from=indi[0]
        self._to=indi[1]
        self._type=indi[2]
    
class distributions:
    indicators = [indicator]
    


# # 11) get_indicator (may be not used)
# - we use “soft” indicators that place uniform probability on satisfying values and decay exponentially in the unsatisfying intervals . [1]
# <img src="ind.PNG" style="width:150;height:200px;">
# The indicator is defined as an array contains 2 appended intervals 


def get_indicator(reduced_int_literal,index_variable_to_be_unchanged): #[1 0 0 5] or [0 -1 0 3]
    indicator=[0]*INDICATOR_NUM_OF_ROWS
    #test if the literal coefficients are all zeros (not exist)
    exist=0
    for i in range(INT_LITERAL_NUM_OF_ROWS):
        if reduced_int_literal[i]!=0:
            exist=1
    if exist==0:
        return indicator
    
    # the literal exists
    maximum=math.pow(2,bit_width_for_int_variables[index_variable_to_be_unchanged]-1)-1
    minimum=-math.pow(2,bit_width_for_int_variables[index_variable_to_be_unchanged]-1)-1
    indicator=[]
    if reduced_int_literal[index_variable_to_be_unchanged]==1:
        # minimum --> -bias
        indicator.append(minimum)
        indicator.append(-reduced_int_literal[-1]) 
        indicator.append(UNIFORM)
        # -bias --> maximum
        indicator.append(-reduced_int_literal[-1])
        indicator.append(maximum) 
        indicator.append(EXP_DOWN)

    if reduced_int_literal[index_variable_to_be_unchanged]==-1:
        # minimum --> bias
        indicator.append(minimum)
        indicator.append(reduced_int_literal[-1]) 
        indicator.append(EXP_UP)
        # bias --> maximum
        indicator.append(reduced_int_literal[-1])
        indicator.append(maximum) 
        indicator.append(UNIFORM)
    
    ind=Indicator(indicator)

    return ind


# # 12) is_int_literal_exist (may not be used)
# to check if it is a literal or not , all coefficients will be zeros if no literal


def is_int_literal_exist(int_literal):
    #test if the literal coefficients are all zeros (not exist)
    exist=False
    for i in range(INT_LITERAL_NUM_OF_ROWS):
        if int_literal[i]!=0:
            exist=True
    return exist


# # 13) get_segments_from_active_formula
# For each clause C, we take the pointwise max (<b>union</b>) of the indicators for relations in C to get an indicator for the clause as a whole. Then we take the pointwise min (<b>intersection</b>) the clause indicators to create a distribution.
# the output should be a list (array) of intervals(segments).



def get_clause(ith_clause,_formula):
    clause=[]
    first_c=ith_clause *CLAUSE_NUM_OF_ROWS
    last_c=first_c+CLAUSE_NUM_OF_ROWS
    clause=_formula[first_c:last_c]
    return clause



def get_int_literal(ith_literal,clause):
    int_literal=[]
    first=(ith_literal*INT_LITERAL_NUM_OF_ROWS)+BOOL_LITERAL_NUM_OF_ROWS
    last=first+INT_LITERAL_NUM_OF_ROWS
    int_literal=clause[first:last]
    return int_literal


print(get_int_literal(0,get_clause(0,formula)))



def get_segments_from_active_clause(active_clause,index_variable_to_be_unchanged):
    case1=[]
    case2=[]
    for i in range(NUM_OF_INT_LITERALS):
        int_literal=get_int_literal(0,active_clause)
        if is_int_literal_exist(int_literal):
            if int_literal[0]>0:
                case1.append(get_indicator(int_literal,index_variable_to_be_unchanged))
            else:
                case2.append(get_indicator(int_literal,index_variable_to_be_unchanged))
        




def get_segments_from_active_formula(active_formula,index_variable_to_be_unchanged):
    clauses_segments=[]
    for i in range(NUM_OF_CLAUSES):
        active_clause=get_clause(i,active_formula)
        clauses_segments.append(get_segments_from_active_clause(active_clause,index_variable_to_be_unchanged))
        
        


# # 14) select_segment
# 


def select_segment(segments,num_segments):
    w=[0]*num_segments #segments_weights
    for i in range(num_segments):
        segment=[]
        first=i*INTERVAL_NUM_OF_ROWS
        last=first+INTERVAL_NUM_OF_ROWS
        #print(first)
        #print(last)
        segment=segments[first:last]
        #print(segment)
        segment_type=segment[2]
        segment_from=segment[0]
        segment_to=segment[1]
        if segment_type==UNIFORM:
            w[i]=segment_to-segment_from+1
        if segment_type== EXP_UP or EXP_DOWN:
            w[i]=((1-(math.exp(-(segment_to-segment_from+1))))/(1-math.exp(-1)))
    probabilities=[]#segments_normalized_probabilities
    #print(w)
    sum_w = sum(w)
    #print(sum_w)
    probabilities = [x / sum_w for x in w]
    #print(probabilities)
    # select segment according to the normalized propabilities p1,p2,p3,...
    selected_segment_number = np.random.choice(range(num_segments), p=probabilities)
    #print(selected_segment_number)
    first=selected_segment_number*INTERVAL_NUM_OF_ROWS
    last=first+INTERVAL_NUM_OF_ROWS
    selected_segment=segments[first:last]
    return selected_segment,w[selected_segment_number]


# # 15) propose_from_segment


def propose_from_segment(segment,w_segment):
    segment_type=segment[2]
    segment_from=segment[0]
    segment_to=segment[1]
    
    if segment_type==UNIFORM:
        proposed_value = random.randint(segment_from, segment_to)
        return proposed_value
    
    theta = random.uniform(0, w_segment)
    d = math.ceil(-1 - math.log(1 - theta * (1 - math.exp(-1))))
    if segment_type== EXP_UP :
        proposed_value = segment_to - d
        return proposed_value
    if segment_type== EXP_DOWN:
        proposed_value = segment_from + d
        return proposed_value


# # 16) propose
'''

def propose(selected_int_variable_index):

    active_formula=get_active_clauses(selected_int_variable_index)
    segments,num_segments=get_segments_from_active_formula(active_formula)
    selected_segment,w_selected_segment=select_segment(segments,num_segments)
    proposed_value=propose_from_segment(selected_segment,w_selected_segment)
    return proposed_value


# # 17) metropolis_move

def metropolis_move():
    
    #select variable bool or int
    if NUM_OF_BOOL_VARIABLES == 0:
        random_variable_is_int_or_bool = random.randint(1, 1)
    else:
        random_variable_is_int_or_bool = random.randint(0, 1)  ## 1 --> int     0-->  bool
    if random_variable_is_int_or_bool == 0:
        # select bool variable
        selected_bool_variable_index = random.choice(range(NUM_OF_BOOL_VARIABLES))
        # flip the value of this selected bool variable
        if current_values_bool[selected_bool_variable_index]==0:
            current_values_bool[selected_bool_variable_index]=1
        elif current_values_bool[selected_bool_variable_index]==1:
            current_values_bool[selected_bool_variable_index]=0
                                                                                                           
        # select int variable
        selected_int_variable_index = random.choice(range(NUM_OF_INT_VARIABLES))
        U = find_number_of_unsatisfied_clauses() 
        proposed_value = propose(selected_int_variable_index)
        # save current int assignment
        last_current_values_int = current_values_int
        # update current int assignment
        current_values_int[selected_int_variable_index] = proposed_value
        # Q calculating
        Q = 0.5
        # U, nU calculating
        nU = find_number_of_unsatisfied_clauses() 
        # take it or not
        pr_do_change = min(1, Q * (math.exp(-((nU - U) / TEMPERATURE))))
        pr_stay = 1 - pr_do_change
        choice = np.random.choice(['do_change', 'stay'], p=[pr_do_change, pr_stay])
        if choice == 'stay':
            current_values_int = last_current_values_int
            return current_values_int
        elif choice == 'do_change':
            # tha change is made already
            return current_values_int


# # 18) local_move (bool part should be modified)


def local_move():
    #1 select unsatisﬁed clause C ∈ ϕ uniformly at random
    unsatisfied_clauses_indices = []
    for i in range(NUM_OF_CLAUSES):
        if check_clause(i)==False:
            unsatisfied_clauses_indices.append(i)
    selected_unsatisfied_clause_index = random.choice(unsatisfied_clauses_indices)

    # bool part
    '''
    '''
    for j in range (NUM_OF_BOOL_LITERALS):
        unsatisfied_clause.bool_literals[i].value =~ unsatisfied_clause.bool_literals[i].value
        value =find_number_of_unsatisfied_clauses()
        if (i == 0):
            min_bool = value
        elif (value < min_bool):
            min_bool = value
    
    '''
    '''
    # int part
    for k in range(NUM_OF_INT_LITERALS):
        int_variables_in_literal=[]
        selected_unsatisfied_clause=[]
        first_c=selected_unsatisfied_clause_index *CLAUSE_NUM_OF_ROWS
        last_c=first_c+CLAUSE_NUM_OF_ROWS
        selected_unsatisfied_clause=formula[first_c:last_c]
        
        int_literal=[]
        first=(k*INT_LITERAL_NUM_OF_ROWS)+BOOL_LITERAL_NUM_OF_ROWS
        last=first+INT_LITERAL_NUM_OF_ROWS
        int_literal=selected_unsatisfied_clause[first:last]
        
        if is_int_literal_exist(int_literal)==True:
            #select random variable that is involved in this literal
            for m in range(NUM_OF_INT_VARIABLES):
                if int_literal[m]!=0:
                    int_variables_in_literal.append(m)
            selected_int_variable_index = random.choice(int_variables_in_literal)
            
            # save current int assignment
            last_current_values_int = current_values_int
            
            old_number = find_number_of_unsatisfied_clauses()
            
            current_values_int[selected_int_variable_index] = propose(selected_int_variable_index)
            new_number = find_number_of_unsatisfied_clauses()
            if (old_number<new_number):
                current_values_int = last_current_values_int
        else :
            continue
            
    return current_values_int


# # 19) solver


def solver():
    #make random assignments
    make_random_assignment_int()
    print('random',current_values_int)
    make_random_assignment_bool()
    #metropolis
    current_int=metropolis_move()
    counter=1
    print(counter,current_int)

    while check_satisfiability()==False: #problem here
        counter+=1
        compute_pls(counter)
        
        choice=np.random.choice(['local','metropolis'], p=[pls,1-pls])
        #choice='metropolis'
        if choice == 'local':
            print("local")
            current_int=local_move()

        elif choice == 'metropolis':
            print("metropolis")
            current_int=metropolis_move()
        print(counter,current_int)


# # Refrences
# [1]http://www.eecs.berkeley.edu/Pubs/TechRpts/2010/EECS-2010-165.html

# In[ ]:




