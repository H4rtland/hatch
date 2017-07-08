import uuid
import sys
from collections import namedtuple
import copy

import time

from compiler.expressions import *

expression_checkers = {}

class checker_for:
    def __init__(self, expression):
        self.expression = expression
    
    def __call__(self, f):
        expression_checkers[self.expression] = f
        return f
    
NamespaceFunction = namedtuple("NamespaceFunction", ["return_type", "args"])
NamespaceVariable = namedtuple("NamespaceVariable", ["type", "is_array"])

class NamespaceGroup:
    def __init__(self, **group):
        self.group = group
        
    def get(self, name, *subnames):
        if isinstance(self.group[name], NamespaceGroup):
            return self.group[name].get(*subnames)
        return self.group[name]
    
    def set(self, *args):
        *path, name, item = args
        if len(path) == 0:
            self.group[name] = item
        else:
            if not path[0] in self.group:
                raise Exception(path, name, item)
            self.group[path[0]].set(*path[1:], name, item)
            
    def contains(self, *args):
        *path, name = args
        if len(path) == 0:
            return name in self.group
        else:
            if not path[0] in self.group:
                return False
            return self.group[path[0]].contains(*args[1:])

    def has_matching_function(self, args, parameters):
        *path, name = args
        if path:
            if not path[0] in self.group:
                return False
            return self.group[path[0]].has_matching_function(args[1:], parameters)
        else:
            if name in self.group:
                return True
            for local_name in self.group:
                if local_name.split("###")[0] == name:
                    function_param_types = [(arg.type, arg.is_array) for arg in self.group[local_name].args]
                    if parameters == function_param_types:
                        return True
            return False

    def get_matching_function(self, args, parameters):
        *path, name = args
        if path:
            return self.group[path[0]].get_matching_function(args[1:], parameters)
        else:
            if name in self.group:
                return self.group[name]
            for local_name in self.group:
                if local_name.split("###")[0] == name:
                    function_param_types = [(arg.type, arg.is_array) for arg in self.group[local_name].args]
                    if parameters == function_param_types:
                        return self.group[local_name]

    def get_matching_function_name(self, args, parameters):
        *path, name = args
        if path:
            return self.group[path[0]].get_matching_function_name(args[1:], parameters)
        else:
            if name in self.group:
                return name
            for local_name in self.group:
                if local_name.split("###")[0] == name:
                    function_param_types = [(arg.type, arg.is_array) for arg in self.group[local_name].args]
                    if parameters == function_param_types:
                        return local_name


    def copy(self):
        return NamespaceGroup(**dict(self.group))
    
    def __repr__(self):
        newline_tab = "\n\t"
        return f"NamespaceGroup({(','+newline_tab).join([name + '=' + str(item) for name, item in self.group.items()])})"

internal_functions = {
    "__internal_print":NamespaceFunction(Types.VOID, [NamespaceVariable(Types.INT, False)]),
    "__internal_print_char":NamespaceFunction(Types.VOID, [NamespaceVariable(Types.CHAR, False)]),
}


class TypeChecker:
    def __init__(self, source, tree, sub_trees):
        self.source = source.split("\n")
        self.tree = tree
        self.sub_trees = sub_trees
        self.checking_expression = None
        
        # Use this identifier to find current function in return checker.
        # Use a uuid to prevent overlap with any user defined function name
        # like "current_function" which could otherwise be used in the namespace.
        self.current_function_identifier = uuid.uuid4().hex
        
    def print_error(self, error):
        time.sleep(0.01)
        print(f"File: {self.checking_expression.source_file}", file=sys.stderr)
        print(f"Line {self.checking_expression.source_line_num}: {self.checking_expression.source_line}", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(0)
        #raise Exception(error)
        
    def check(self):
        def checker(t, st):
            for tree_name, (tree, sub_trees) in st.items():
                checker(tree, sub_trees)
            namespace = NamespaceGroup(**internal_functions)
            for tree_name, (tree, sub_trees) in st.items():
                module = NamespaceGroup()
                for declaration in tree:
                    if isinstance(declaration, Function):
                        args = [NamespaceVariable(TypeManager.get_type(arg[0].lexeme), arg[3]) for arg in declaration.args]
                        module.set(declaration.name.lexeme, NamespaceFunction(TypeManager.get_type(declaration.rtype.lexeme), args))
                    #elif isinstance(declaration, Let):
                    #    module.set(declaration.name, NamespaceVariable(declaration.vtype.lexeme, declaration.array))
                namespace.set(tree_name, module)
            for function in t:
                args = [NamespaceVariable(TypeManager.get_type(arg[0].lexeme), arg[3]) for arg in function.args]
                #namespace[function.name.lexeme] = NamespaceFunction(TypeManager.get_type(function.rtype.lexeme), args)
                namespace.set(function.name.lexeme, NamespaceFunction(TypeManager.get_type(function.rtype.lexeme), args))

            try:
                for function in t:
                    self.check_branch(function, namespace)
            except ExpressionValidationException as e:
                self.print_error(str(e))

        checker(self.tree, self.sub_trees)
            
    def check_branch(self, branch, namespace):
        if branch.__class__ in expression_checkers:
            # copy namespace so modifications only get passed down, not back up
            self.checking_expression = branch
            expression_checkers[branch.__class__](self, branch, namespace.copy())
        elif branch is None:
            # e.g, no else block in If expression
            # ignore silently
            pass
        else:
            print(f"TypeChecker: Unchecked branch: {branch.__class__.__name__}")
            
    @checker_for(Function)
    def check_function(self, function, namespace):
        namespace.set(self.current_function_identifier, namespace.get(function.name.lexeme))
        for arg in function.args:
            # namespace[arg[1].lexeme] = Let(arg[0], arg[1].lexeme, 0, False, 0)
            # print(arg)
            namespace.set(arg[1].lexeme, NamespaceVariable(TypeManager.get_type(arg[0].lexeme), arg[3]))
        self.check_branch(function.body, namespace)
        
    @checker_for(Block)
    def check_block(self, block, namespace):
        for statement in block.statements:
            self.check_branch(statement, namespace)
            if isinstance(statement, Let):
                # namespace[statement.name.lexeme] = statement
                namespace.set(statement.name.lexeme, NamespaceVariable(TypeManager.get_type(statement.vtype.lexeme), statement.array))
            
    @checker_for(If)
    def check_if(self, if_statement: If, namespace):
        if not if_statement.condition.resolve_type(namespace) == Types.BOOL:
            self.print_error("If statement did not receive boolean expression")
        self.check_branch(if_statement.then, namespace)
        self.check_branch(if_statement.otherwise, namespace)


    @checker_for(Return)
    def check_return(self, return_statement: Return, namespace):
        current_function = namespace.get(self.current_function_identifier)#namespace[self.current_function_identifier]
        if not return_statement.resolve_type(namespace) == current_function.return_type:
            self.print_error(f"Return type mismatch: {return_statement.resolve_type(namespace)} != {current_function.return_type}")
            
    @checker_for(Let)
    def check_let(self, let_statement: Let, namespace):
        if TypeManager.get_type(let_statement.vtype.lexeme) == Types.VOID:
            self.print_error("Cannot create a void variable")
        if not TypeManager.get_type(let_statement.vtype.lexeme) == let_statement.initial.resolve_type(namespace):
            self.print_error(f"Let statement type mismatch: "
                             f"{TypeManager.get_type(let_statement.vtype.lexeme)} != {let_statement.initial.resolve_type(namespace)}")
            
    @checker_for(Call)
    def check_call(self, call_statement: Call, namespace):
        call_statement.resolve_type(namespace)
        
    @checker_for(Assign)
    def check_assign(self, assign_statement: Assign, namespace):
        assigning_to_type = namespace.get(assign_statement.name).type
        assigned_type = assign_statement.value.resolve_type(namespace)
        if not assigning_to_type == assigned_type:
            self.print_error(f"Assignment type mismatch: {assigning_to_type} != {assigned_type}")
            
    @checker_for(For)
    def check_for(self, for_loop: For, namespace):
        self.check_branch(for_loop.declare, namespace)
        if isinstance(for_loop.declare, Let):
            namespace.set(for_loop.declare.name.lexeme,
                          NamespaceVariable(TypeManager.get_type(for_loop.declare.vtype.lexeme),
                                            for_loop.declare.array))
        self.check_branch(for_loop.condition, namespace)
        if not for_loop.condition.resolve_type(namespace) == Types.BOOL:
            self.print_error("Expected boolean expression for while loop condition")
        self.check_branch(for_loop.action, namespace)
        self.check_branch(for_loop.block, namespace)
        
    @checker_for(While)
    def check_while(self, while_loop: While, namespace):
        self.check_branch(while_loop.condition, namespace)
        if not while_loop.condition.resolve_type(namespace) == Types.BOOL:
            self.print_error("Expected boolean expression for while loop condition")
        self.check_branch(while_loop.block, namespace)
        
    @checker_for(Binary)
    def check_binary(self, binary: Binary, namespace):
        binary.resolve_type(namespace)