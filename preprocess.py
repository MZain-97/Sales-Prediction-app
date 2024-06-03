import streamlit as st
import pandas as pd
from scipy.optimize import linprog
import numpy as np
import pulp
from pulp import *
from sklearn.linear_model import LinearRegression
from pyomo.environ import *

def optimize_data(unpivoted_baseline, product_group_totals, end_usage_totals):
    for year in range(2024, 2031):
        # Extract the values for the current year
        year_data = unpivoted_baseline[unpivoted_baseline['Year'] == year]

        # Create a model
        model = ConcreteModel()

        # Initialize decision variables
        model.variables = Var(year_data.index, domain=NonNegativeReals)

        # Define the objective function
        def objective_rule(model):
            return sum(model.variables[idx] for idx in year_data.index)
        model.obj = Objective(rule=objective_rule, sense=maximize)

        # Add constraints for Product Group totals
        def product_group_constraint_rule(model, group):
            group_data = year_data[year_data['Product Group'] == group]
            total_value = product_group_totals[
                (product_group_totals['Product Group'] == group) &
                (product_group_totals['Year'] == year)]['Value'].values[0]
            return sum(model.variables[idx] for idx in group_data.index) == total_value
        model.product_group_constraints = Constraint(year_data['Product Group'].unique(), rule=product_group_constraint_rule)

        # Add constraints for End Usage Level 2 totals
        def end_usage_constraint_rule(model, usage):
            usage_data = year_data[year_data['End Usage Level 2'] == usage]
            total_value = end_usage_totals[
                (end_usage_totals['End Usage Level 2'] == usage) &
                (end_usage_totals['Year'] == year)]['Value'].values[0]
            return sum(model.variables[idx] for idx in usage_data.index) == total_value
        model.end_usage_constraints = Constraint(year_data['End Usage Level 2'].unique(), rule=end_usage_constraint_rule)

        # Add constraints for deviation from check file values
        def lower_deviation_constraint_rule(model, idx):
            check_value = year_data.loc[idx, 'Value']
            lower_bound = check_value * 0.1  # 10% lower bound
            return model.variables[idx] >= lower_bound
        def upper_deviation_constraint_rule(model, idx):
            check_value = year_data.loc[idx, 'Value']
            upper_bound = check_value * 2  # 200% upper bound
            return model.variables[idx] <= upper_bound
        model.lower_deviation_constraints = Constraint(year_data.index, rule=lower_deviation_constraint_rule)
        model.upper_deviation_constraints = Constraint(year_data.index, rule=upper_deviation_constraint_rule)

        # Solve the optimization problem
        solver = SolverFactory('glpk')
        results = solver.solve(model)

        # Update the original DataFrame with the optimized values
        for idx in year_data.index:
            unpivoted_baseline.loc[idx, 'Value'] = model.variables[idx].value

    return unpivoted_baseline
