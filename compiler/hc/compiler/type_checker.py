import uuid
import sys
from collections import namedtuple
import copy
import contextlib

import time

from compiler.expressions import *

expression_checkers = {}

class checker_for:
    def __init__(self, *expressions):
        self.expressions = expressions
    
    def __call__(self, f):
        for expression in self.expressions:
            expression_checkers[expression] = f
        return f
    
NamespaceFunction = namedtuple("NamespaceFunction", ["return_type", "args"])
NamespaceVariable = namedtuple("NamespaceVariable", ["type", "is_array"])

class NamespaceGroup:
    def __init__(self, **group):
        self.group = group
        
    def get(self, name, *subnames):
        if isinstance(self.group[name], NamespaceGroup) and len(subnames) > 0:
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

CallFromTo = namedtuple("CallFromTo", ["from_func", "to_func"])

class TypeChecker:
    def __init__(self, source, tree, sub_trees):
        self.source = source.split("\n")
        self.tree = tree
        self.sub_trees = sub_trees
        self.all_calls = []
        
        # Use this identifier to find current function in return checker.
        # Use a uuid to prevent overlap with any user defined function name
        # like "current_function" which could otherwise be used in the namespace.
        self.current_function_identifier = uuid.uuid4().hex
        self.current_function_name = None
        
    def print_error(self, error):
        time.sleep(0.01)
        with contextlib.redirect_stdout(sys.stderr):
            print(f"File: {self.checking_expression.source_file}")
            print(f"Line {self.checking_expression.source_line_num}: {self.checking_expression.source_line}")
            print(error)
        sys.exit(0)
        #raise Exception(error)
        
    def check(self):
        def checker(t, st):
            for tree_name, (tree, sub_trees) in st.items():
                checker(tree, sub_trees)

            namespace = NamespaceGroup(**internal_functions)
            type_manager = TypeManager()
            for tree_name, (tree, sub_trees) in st.items():
                module = NamespaceGroup()
                for declaration in tree:
                    if isinstance(declaration, Function):
                        args = [NamespaceVariable(type_manager.get_type(arg.type.lexeme), arg.is_array) for arg in declaration.args]
                        module.set(declaration.name.lexeme, NamespaceFunction(type_manager.get_type(declaration.rtype.lexeme), args))
                    #elif isinstance(declaration, Let):
                    #    module.set(declaration.name, NamespaceVariable(declaration.vtype.lexeme, declaration.array))
                namespace.set(tree_name, module)
            for branch in t:
                if isinstance(branch, Struct):
                    internal_structure = {}
                    for position, (member_type, name) in enumerate(branch.members, start=1):
                        internal_structure[name.lexeme] = (position, type_manager.get_type(member_type.lexeme))
                    struct_type = Type(branch.name.lexeme, len(branch.members), internal_structure=internal_structure)
                    type_manager.define_type(struct_type)
                    #struct = NamespaceGroup()
                    #for member_type, name in branch.members:
                    #    struct.set(name.lexeme, NamespaceVariable(TypeManager.get_type(member_type.lexeme), False))
            for branch in t:
                if isinstance(branch, Function):
                    args = [NamespaceVariable(type_manager.get_type(arg.type.lexeme), arg.is_array) for arg in branch.args]
                    #namespace[function.name.lexeme] = NamespaceFunction(TypeManager.get_type(function.rtype.lexeme), args)
                    namespace.set(branch.name.lexeme, NamespaceFunction(type_manager.get_type(branch.rtype.lexeme), args))

            try:
                for function in t:
                    self.check_branch(function, namespace, type_manager)
            except ExpressionValidationException as e:
                self.print_error(str(e))


        checker(self.tree, self.sub_trees)

        included_functions = {"main",}
        last_size = 0
        while len(included_functions) > last_size:
            last_size = len(included_functions)
            for call in self.all_calls:
                if call.from_func in included_functions:
                    included_functions.add(call.to_func)

        return included_functions
            
    def check_branch(self, branch, namespace, type_manager):
        if branch.__class__ in expression_checkers:
            # copy namespace so modifications only get passed down, not back up
            self.checking_expression = branch
            expression_checkers[branch.__class__](self, branch, namespace.copy(), type_manager)
        elif branch is None:
            # e.g, no else block in If expression
            # ignore silently
            pass
        else:
            print(f"TypeChecker: Unchecked branch: {branch.__class__.__name__}")
            
    @checker_for(Function)
    def check_function(self, function, namespace, type_manager):
        self.current_function_name = function.name.lexeme
        namespace.set(self.current_function_identifier, namespace.get(function.name.lexeme))
        for index, arg in enumerate(function.args):
            # namespace[arg[1].lexeme] = Let(arg[0], arg[1].lexeme, 0, False, 0)
            # print(arg)
            if type_manager.get_type(arg.type.lexeme).has_internal_structure:
                group = NamespaceGroup()
                group.type = type_manager.get_type(arg.type.lexeme)
                group.is_array = False
                struct_type = type_manager.get_type(arg.type.lexeme)
                for name, (position, type_) in struct_type.internal_structure.items():
                    group.set(name, NamespaceVariable(type_, False))
                group.internal_structure = struct_type.internal_structure
                namespace.set(arg.name.lexeme, group)
                function.args[index] = arg._replace(is_struct=True)
            else:
                namespace.set(arg.name.lexeme, NamespaceVariable(type_manager.get_type(arg.type.lexeme), arg.is_array))
        self.check_branch(function.body, namespace, type_manager)
        
    @checker_for(Block)
    def check_block(self, block, namespace, type_manager):
        for statement in block.statements:
            self.check_branch(statement, namespace, type_manager)
            if isinstance(statement, Let):
                # namespace[statement.name.lexeme] = statement
                if isinstance(statement.initial, StructCreate):
                    group = NamespaceGroup()
                    struct_type = type_manager.get_type(statement.vtype.lexeme)
                    group.type = struct_type
                    group.is_array = False
                    for name, (position, type_) in struct_type.internal_structure.items():
                        group.set(name, NamespaceVariable(type_, False))
                    group.internal_structure = struct_type.internal_structure
                    namespace.set(statement.name.lexeme, group)
                else:
                    namespace.set(statement.name.lexeme, NamespaceVariable(type_manager.get_type(statement.vtype.lexeme), statement.array))
            
    @checker_for(If)
    def check_if(self, if_statement: If, namespace, type_manager):
        if not if_statement.condition.resolve_type(namespace, type_manager) == Types.BOOL:
            self.print_error("If statement did not receive boolean expression")
        self.check_branch(if_statement.then, namespace, type_manager)
        self.check_branch(if_statement.otherwise, namespace, type_manager)


    @checker_for(Return)
    def check_return(self, return_statement: Return, namespace, type_manager):
        current_function = namespace.get(self.current_function_identifier)#namespace[self.current_function_identifier]
        if not return_statement.resolve_type(namespace, type_manager) == current_function.return_type:
            print(return_statement)
            self.print_error(f"Return type mismatch: {return_statement.resolve_type(namespace, type_manager)} != {current_function.return_type}")
        self.check_branch(return_statement.value, namespace, type_manager)
            
    @checker_for(Let)
    def check_let(self, let_statement: Let, namespace, type_manager):
        if type_manager.get_type(let_statement.vtype.lexeme) == Types.VOID:
            self.print_error("Cannot create a void variable")
        if not type_manager.get_type(let_statement.vtype.lexeme) == let_statement.initial.resolve_type(namespace, type_manager):
            self.print_error(f"Let statement type mismatch: "
                             f"{type_manager.get_type(let_statement.vtype.lexeme)} != {let_statement.initial.resolve_type(namespace, type_manager)}")
        self.check_branch(let_statement.initial, namespace, type_manager)
            
    @checker_for(Call)
    def check_call(self, call_statement: Call, namespace, type_manager):
        call_statement.resolve_type(namespace, type_manager)

        for arg in call_statement.args:
            self.check_branch(arg, namespace, type_manager)

        calling_to = call_statement.get_calling_to_name(namespace, type_manager)
        self.all_calls.append(CallFromTo(self.current_function_name, calling_to))
        
    @checker_for(Assign)
    def check_assign(self, assign_statement: Assign, namespace, type_manager):
        assigning_to_type = namespace.get(assign_statement.name).type
        assigned_type = assign_statement.value.resolve_type(namespace, type_manager)
        if not assigning_to_type == assigned_type:
            self.print_error(f"Assignment type mismatch: {assigning_to_type} != {assigned_type}")
        self.check_branch(assign_statement.value, namespace, type_manager)
            
    @checker_for(For)
    def check_for(self, for_loop: For, namespace, type_manager):
        self.check_branch(for_loop.declare, namespace, type_manager)
        if isinstance(for_loop.declare, Let):
            namespace.set(for_loop.declare.name.lexeme,
                          NamespaceVariable(type_manager.get_type(for_loop.declare.vtype.lexeme),
                                            for_loop.declare.array))
        self.check_branch(for_loop.condition, namespace, type_manager)
        if not for_loop.condition.resolve_type(namespace, type_manager) == Types.BOOL:
            self.print_error("Expected boolean expression for while loop condition")
        self.check_branch(for_loop.action, namespace, type_manager)
        self.check_branch(for_loop.block, namespace, type_manager)
        
    @checker_for(While)
    def check_while(self, while_loop: While, namespace, type_manager):
        self.check_branch(while_loop.condition, namespace, type_manager)
        if not while_loop.condition.resolve_type(namespace, type_manager) == Types.BOOL:
            self.print_error("Expected boolean expression for while loop condition")
        self.check_branch(while_loop.block, namespace, type_manager)
        
    @checker_for(Binary)
    def check_binary(self, binary: Binary, namespace, type_manager):
        binary.resolve_type(namespace, type_manager)
        self.check_branch(binary.left, namespace, type_manager)
        self.check_branch(binary.right, namespace, type_manager)

    @checker_for(Literal, Variable)
    def check_pass(self, boring_expression, namespace, type_manager):
        pass