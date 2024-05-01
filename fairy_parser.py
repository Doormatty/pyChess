from lark import Lark, Transformer, v_args, Tree, UnexpectedInput, UnexpectedToken


class MoveTransformer(Transformer):

    def __init__(self):
        super().__init__()
        self.move_dict = {"condition": [],
                          "move_type": [],
                          "distance": [],
                          "direction": []}

    @v_args(inline=True)
    def start(self, items):
        return items[0]

    @staticmethod
    def full_move(items):
        return items

    @staticmethod
    def direction(items):
        if len(items) == 1:
            return {"type": "direction", "value": items[0].value}
        return ",".join([item.type for item in items])

    @staticmethod
    def dist(items):
        return items[0].value

    @staticmethod
    def normal_distance(items):
        return {"type": "normal_move", "value": items[0]}

    @staticmethod
    def range_distance(items):
        return {"type": "range", "min": items[0], "max": items[1]}

    @staticmethod
    def leaping_distance(items):
        return {"type": "leap", "value": f"{items[0]}/{items[1]}"}

    @staticmethod
    def move_distance(items):
        return items[0]

    @staticmethod
    def move_type(items):
        if items[0] is None:
            return {"type": "move_type", "value": "normal"}
        else:
            if len(items) == 1:
                return {"type": "move_type", "value": items[0].value}

    @staticmethod
    def condition(items):
        if items[0] is None:
            return {"type": "condition", "value": "None"}
        else:
            return {"type": "condition", "value": items[0].value}

    @staticmethod
    def move(items):
        if len(items) == 1:
            return items[0]
        else:
            return {"type": "composite_move", "components": items}

    @staticmethod
    def then_move(items):
        return {"type": "sequence", "moves": items}

    @staticmethod
    def repeated_move(items):
        return {"type": "repeat", "moves": items}

    @staticmethod
    def pick_one_move(items):
        return {"type": "pick_one", "moves": items}

    def basic_move(self, *args):
        for arg in args:
            if isinstance(arg, list):
                for ar in arg:
                    self.process_element(ar)
            else:
                self.process_element(arg)

    def process_element(self, element):
        if isinstance(element, Tree):
            print(1)
        element_type = element.get('type', None)
        if element_type is not None:
            if element_type in ("range", "normal_move", "leap"):
                self.move_dict["move_type"] = element.get('value')
                # self.move_dict["distance"]["type"]
            else:
                try:
                    self.move_dict[element_type].append(element.get('value'))
                except KeyError:
                    print(1)


new_failed = []


def test_moves(move_list, filename):
    with open(filename, 'r') as infile:
        parser = Lark(infile, start='move', parser='lalr', debug=True, transformer=MoveTransformer())
    for move in move_list:
        try:
            # print(f"Parsing move: {move}")
            parse_tree = parser.parse(move)
            print(parse_tree)
        except Exception as e:
            print(f"ERROR: Failed to parse move {move}:\n {str(e)}")
            new_failed.append(move)
    print(new_failed)


failed = ['n+, 1X', 'o1>, c1X>', 'n+.nX, nX.n+', 'on+, cnX', 'o1>, c1X>, io2>', '1*>, io2>', 'nX>, n<, 1*, 2X<', '1-4X, 2+', '1*,^n*', 'cn(^nX), o1X', '1*, 2*', 'n*>=, ~1/2<, 1*<', '1X, 1<>, 1=', 'n<>, 1+, 1X>', '1X, ~2*', '~1/2, 1-2X, ~2+', '~1/2.n+', '1+, ~ 1/2, ~ 3+', '1+, ~2*', '1*, o2>', '1>, io2>', '~0/0', 'n*', 'n=, 1+', 'o2+, c1X', 'n(~2*)', 'n>, 2<', '1/3, 2/3', 'on*', '1*>', '~1/2, ~1/4', '1X, 1<>', '1*,c2*', '1+,~1/2', 'nX, 1+', '~0/2, ~1/2, ~2/2', '1+, ~1/2, ~1/3',
          '1-2+,nX', 'c^n*, on*', 'n>, 1X, 1<', 'cn(^nX), onX', '1X, ~3+', 'n(2*),1*', 'cn(^2X^4+), o1X>', '~1/2, ~2*', '1X, 1>', '~1/2, ~1/3,nX', 'n(2/3)', 'n(~2+)', 'cnX, o^nX', '~1/2>, nX<', '~1/3, ~3+', 'onX,cn+', '1*, ~1/3', '~2/3', 'cn+, o^n+', 'n+, n(~1/2)', 'n+,1-3X', '~1/2, ~1/3, ~2/3', 'o1>, c1X>, io2>, ~1/2', 'n<>, 1*, 3X>', 'n+, nX<, 1X>, ~2X>', '1X, ~2+', '~1-2*<>', '~1/5', 'n>=, 1*<', '1=, 1X>', '~2X, ~3+', 'n+, nX>', 'n<>, nX<', 'o~1/2, cn*', 'cn(^2X>), o1X>', 'n<>, 1+',
          'n+, ~1/2, 1X', 'nX, n=, 2X>', 'cn*, o^n*', '1*, ^n(~1/2)', 'n+, 1+.nX', '1X, ~1/3', '3X,~1/3', '~1/2<>, 1X', 'nX,n(~2+)', 'c~1/2', '1=, 2X>', '~1/2>, ~2/1<', 'n+,1X.n+', '1*, ~1/3, ~2/3', '~2+, ~1/2', '1-2+, ~1/2', '2+.nX', '1X.n+', '1X, 1<=', '~1/2, ~2X', '~2>, 1X<', 'on+,c^n+', 'nX, 1X.n+', '4X,~1/2', 'n(3+)', '1-4+', '1+.nX', '~1/3', 'cn(^n+), on+', '1X, ~2+, ~3+', '^n(~1/2)', 'o1+, c1X', '1X.n<>', '1<=, 1X>', 'o1*, cn*', '1+, ~2X', '~1/2.nX',
          '~2*, c1*', 'n(1/2)', 'nX, ~1/2, 1+', 'n*, ~1/2', '1X.n+, n+.1X', 'n(1/3)', '~2/4', '~1/2, ~1/3', 'n<>, nX>', '1=, 1X', 'nX, ~1/2, 1+', '~1/2', 'o1>=, c1X>', '1+, 1X>', '3+,o~2+,o~3+', '~5+, ~3/4', '~1/4.n+', '1+,~2+, ~1/2', 'o1>, c1*>, io2>', '~1/4', 'cn(^2>=), o1*>=', '~1/7, ~5X', '~2+, ~3+', 'n+, ~1/2', '1+.nX', '~1/2, 1*', '1*, ~2*', '1*, c(n*>)', 'nX, ~1/3', 'cn(^2*>=), o1X>', '~2/1>, ~1/2<', '~2/2, ~3/3, ~0/2, ~0/3', '1X>, o1>, io2>',
          '~1/2, ~1/3, n+', 'c^nX, onX', '1>, 1X<', '~1/6', '1-2X>,1>=', '3=, 1X>, 1+<', '1X, ~2X', 'cn*, c~1/2', 'o1>, o2>, c1X>', 'n*, ~n(1/2)', '1+.nX, nX.1+', '1*, ~2/2, ~3/3, ~0/2, ~0/3', 'nX, ~1/2', '1=, ~2<>', 'cn(^2>=), o1*>', '~1/4,~2/3', '1*, ~2X', 'n>, 1<', 'cn(^2*), o1*>', 'nX, n=', '1+, ~2/3', '~2X, ~2/2', '2*', 'nX, n(1/2)', 'n>, nX<', '1*, ~2*, ~(1/2)', 'nX', 'n>, n=, 2/1>, 1*', '1*, ~2*, ~1/2', '1<>.nX', '~2X>, ~2<', 'o1>, c1X>, o2>',
          '1+, 2X>', '~2+, 1/2, 3X', '1X, ~2X, ~1/2', 'nX, ~2+', 'cn(^n+), on*', 'cn(^2X), o1X>', '~3/3, ~5/5, ~0/15', 'o1+,c1X', '~1/3, ~2/3', '1*>=, o1<, o2<, o1X<, o2X<', 'o1>, c1X>, io2>, ~1/3', 'n(~2X)', '~2*, o1*', 'o1*, cn(^2*)', '~3X, ~2/4, ~1/5', 'o1>=&c1X>', 'n>, nX<, 1X', 'nX, n<>', '1*, ~2+, ~1/2', 'n<>, 2=, nX>', '1+,~2X', '1*>, o1<, o2<', 'n>, nX<, 1X<', '~1/3.nX', '1/2', 'n+, ~1/3', 'o1>, c1X>, io2>, o~1/2>', '1*', 'nX,1+.nX', 'nX>, ~1/2<', '1>=, 1X>',
          'c^n(~1/2), on(~1/2)', 'cn*, o1*', '1<>.nX>', 'on*, c~1/2', '1*>, io2*>', 'n(~1/2), n(~1/3)', '~1/3, ~1/4', '1X, 1-4+', 'cn(^nX), o1X>', '~3/4', 'cn(^2X), o1X', 'nX, 1>', 'on*, c^n*', 'nX, n>', '2X.n+', 'o1>, c1X>,~ 0/3,~ 3/3', 'c^n+, on+', '1*, ~2+', '1*>, 1<', '1*, ~1/2', 'o1>, c1X>, io3>', '2(~1/2), 1-4+', 'c~1/2, o1/2', '1-4>, 1X<', 'cn(^2>=), o1>=', 'o1*>, c1*>', 'on>, cnX>', 'o1X>, c1>, io2X>', '2+, 2X, ~1/2, ~1/3', '1+, ~3+', '~1/2, ~3/4', 'n*, n(~1/2)', '1X,~1/2',
          '~2=, ~1/2<>', 'nX, n<=, 1>, ~2>', '2/3', '~1/2, ~2/3', 'o1X>, c1>=, io2X>', '1*, ~2+, ~2X', '1X.n+, 1+.nX', '1X, 1<', '~1/2, ~1/3,n*', 'cn(^nX^2n+), onX', '~2/3.nX', 'nX>, n<', 'n<>, 1*', '1X, 1>=', '~2/2, ~1/3']

test_moves(failed, filename='fairy.lark')
