### Conditions under which the move may occur (lowercase alphanumeric, except n)
* `<blank>` Default – May occur at any point in the game
* `i` May only be made on the initial move (e.g. pawn's 2 moves forward)
* `c` May only be made on a capture (e.g. pawn's diagonal capture)
* `o` May not be used for a capture (e.g. pawn's forward move)

### Move type
* `<blank>` Default – Captures by landing on the piece; blocked by intermediate pieces
* `~` Leaper (leaps); captures by landing on the opposing piece
* `^` Locust (captures by hopping; implies hopper); final move is one square past the captured piece

### Distance (numbers, n)
 * `1` – a distance of one (i.e. to adjacent square)
 * `2` – a distance of two
 * `n` – any distance in the given direction

### Direction (punctuation, X)
* `>`  orthogonally forwards
* `<`  orthogonally backwards
* `<>` orthogonally forwards and backwards
* `=`  orthogonally sideways
* `>=` orthogonally forwards or sideways
* `<=` orthogonally backwards or sideways
* `+`  orthogonally (four possible directions)
* `X`  diagonally (four possible directions)
* `X>` diagonally forwards
* `X<` diagonally backwards
* `*` orthogonally or diagonally (all eight possible directions); same as +X

### Grouping
* `/` two orthogonal moves separated by a slash denote a hippogonal move (i.e. jumps like a knight)
* `&` repeated movement in the same direction, such as for hippogonal riders (e.g., the nightrider)
* `.` then, (e.g., an aanca is 1X.n+; one step diagonally and then any distance orthogonally outwards)
    

### Grouping (punctuation)
* `,` – separates move options; only one of the comma-delimited options may be chosen per move
* () grouping operator; see nightrider
* `-`range operator

Order (not including grouping) is: `<conditions> <move type> <distance> <direction>`

On this basis, the traditional chess moves (excluding castling and en passant capture) are:

* King: `1*`
* Queen: `n*`
* Bishop: `nX`
* Rook: `n+`
* Pawn: `o1>, c1X>, oi2>`
* Knight: `~1/2`

```python
failed = ['2+.nX', '1X.n+', '4X,~1/2', '~1/2, ~1/3, n+', '~1/2, ~1/3,nX', '~1/2, ~1/3,n*', 'n+, 1X', '~2X, ~2/2', 'n(~2X)', 'n(~2*)', 'n*, ~1/2', 'n*, n(~1/2)', '1+.nx', 'n+, 1+.nX', '1-2X>,1>=', '~3/4', '1*', 'nX, ~1/2', 'nX', 'n+, ~1/2, 1X', 'c^nX, onX', 'c^nX, onX', 'o2+, c1X', '1*,c2*', '~1/3.nX', '~1/2, ~1/4', '1-4X, 2+', 'nX, n(1/2)', '~2/1>, ~1/2<', 'o1*>, c1*>', '~0/2, ~1/2, ~2/2', 'nX, ~2+', 'o1X>, c1>, io2X>', 'o1X>, c1>=, io2X>', 'onX,cn+', 'nX>, ~1/2<', '~1/3, ~2/3', '1<=, 1X>', '1=, 1X',
          '1X, 1<=', '2*', '~1/2, ~1/3, ~2/3', 'nX, ~1/3', '1+,~2X', '~1/3', 'n(1/3)', 'c^n+, on+', '1*, ~2+, ~1/2', 'n+, ~1/3', 'nX, ~1/2', '~2+, ~1/2', '~0/2, ~1/2, ~2/2', '1X.n+, n+.1X', '~1/2, 1*', 'nX, ~1/2', '~0/2, ~1/2, ~2/2', '1+, ~2*', '1*, ~2+', 'n+, ~1/2', 'n+, ~1/2', 'n>=, 1*<', 'cn(^2X>), o1X>', 'cn(^2*>=), o1X>', 'cn(^2*), o1*>', 'cn(^2X), o1X>', 'cn(^nX), o1X>', 'cn(^2X^4+), o1X>', 'cn(^2>=), o1>=', 'cn(^2>=), o1*>', 'cn(^2>=), o1*>=', 'cn(^2X), o1X',
          'cn(^2*), o1*or cn(^n*), on*', 'cn(^nX), onX', 'cn(^nX), o1X', 'cn(^nX^2n+), onX', 'cn(^n+), on+', 'cn(^n+), on*', '1-4>, 1X<', 'n<>, 1*, 3X>', 'n>, n=, 2/1>, 1*', '1*>, o1<, o2<', '1*>=, o1<, o2<, o1X<, o2X<', '1*>, 1<', '1X>, o1>, io2>', '~1/2>, ~2/1<', '1*, n>; n=; n<', 'c^nX, onX', 'nX, 1+', 'n+, 1X', 'nX, ~1/2, 1+', '~0/2n', 'n(~2+)', '1>, 1X<', '3+,o~2+,o~3+', '1=, ~2<>', 'o1>, c1X>, io2>, ~1/2', 'nX, 1+', 'n+, 1X', '1X, 1>=', '1*, ~2/2, ~3/3, ~0/2, ~0/3', '1+.nX, nX.1+',
          '1X, ~2+', '1-2+, ~1/2', '1X,~1/2', 'o1>=  c1X>', 'nX>, n<, 1*, 2X<', '1X.n+', 'n*', 'n*', '~2/3', '1X, 1>', '2/3', '1X, ~2X', '1*, ~2+, ~2X', 'n*, n~(1/2)', '1+,~1/2', 'n+, ~1/2', 'onX,cn+', '1>=, 1X>', '1X, ~2*', '1X, ~2X', 'nX>, n<', '1/3, 2/3', '3X,~1/3', 'cn+, o^n+', '1X, ~2X', '1X, 1<>', '~1/2<>, 1X', '~5+, ~3/4', '~1/6', '1=, 1X>', 'nX, ~1/3', 'nX, 1>', '1+, 2X>', 'n(2*),1*', 'nX, n<>', 'n<>, 1*', 'n*>=, ~1/2<, 1*<', '1X, 1-4+', '1X, ~2+', '~2+, 1/2, 3X', 'nX, n=, 2X>',
          'nX, n=', 'n+, nX>', 'nX, n>', '1X, ~3+', 'o1+, c1X', 'nX,n(~2+)', '1*, ~1/3', '~1/4', '~2/3', '~1/4.n+', '~2*, o1*', '~1/3', '~1/2, ~1/3', 'n(~1/2), n(~1/3)', '1X.n+, 1+.nX', '1+, 1X>', '~2X>, ~2<', '1*>, io2*>', 'n<>, 2=, nX>', '1X.n+', 'on+, cnX', '1X, ~2+, ~3+', '~2/4', 'nX,1+.nX', '~2/2, ~3/3, ~0/2, ~0/3', 'n+, ~1/2, 1X', '2*', '1X, ~2X, ~1/2', 'c~1/2', 'o1+, c1X', 'nX, n<=, 1>, ~2>', '1/2', '~1/2, ~2X', 'n>, 1<', 'n>, nX<', '1+, ~ 1/2, ~ 3+', '~1/5',
          'on*', '~1/2, ~3/4', '1*>', '~1/2, ~2*', '1*, ~2*, ~1/2', '~1/2, 1*', '~1/2, ~2X', '1X, 1>', '1X, ~2+', '~2=, ~1\\2<>', 'o~1/2, cn*', '~1/2', '~1/2>, nX<', '~2/4', '1X, 1<>, 1=', 'n>, nX<, 1X', 'on*, c^n*', '~1/3, ~3+', '~1/2, n2', 'n>, 2<', '1*, c(n*>)', '1*, ~2*, ~(1/2)', '1*, ~2*, ~1/2', '~2*, c1*', 'o1>, c1X>, io2>, ~1/3', 'cnX, o^nX', 'c^n*, on*', '~1-2+ = 1+, ~2+', 'n*, ~1/2', '1*, ~2*', '1+.nX', '1/2', '1+,~1/2', 'n+, ~1/2', '1*, ~2*', 'o1*, cn*', 'cn*, c~1/2', 'n(1/3)',
          'nX, 1X.n+', '1+,~2+, ~1/2', 'nX, ~1/2', 'nX, 1+', '1/2', 'o1*, cn(^2*)', '1*, ~1/2', '2(~1/2), 1-4+', 'c^n(~1/2), on(~1/2)', '~2X, ~3+', 'n(1/2)', '^n(~1/2)', '~1/2, ~2/3', '1X, 1<', '2X.n+', '~1/2, 1*', 'nX, ~1/2', '1*, ^n(~1/2)', 'c^n+, on+', '1*, ~2*', 'o1>, c1X>, io2>', '1>; 1>, 1+=', '1>=, 1X>', 'o1>, c1X>', 'o1>, c1X>, io3>', 'o1>, o2>, c1X>', 'o1X>, c1>, io2X>', '~1/4 ~2/3', '~1/2.n+', '~2>, 1X<', '1+, ~2X', 'nx, ~1/2, 1+', '1X,~1/2', '~1/2, ~2X', '1X,~1/2', '1*, o2>',
          '1*, ~2X', 'nX, ~1/2', '~3/3, ~5/5, ~0/15', 'o1+,c1X', 'n*, ~n(1/2)', 'on*, c~1/2', 'n<>, 1+, 1X>', 'n+, n(~1/2)', 'n+,1X.n+', 'nX', '1+.nX', 'n+,1-3X', '1X, 1<>, 1=', 'n>, nX<, 1X<', '~2/2 ~1/3', 'on+,c^n+', '~5+, ~3/4', '~1/7, ~5X', 'n(1/2)', 'on+, cnX', 'cn*, o1*', '1-2+,nX', 'n>, 1X, 1<', 'c~1/2, o1/2', '1*n^*', 'o1>, c1X>, io2>, o~1/2>', '1+, ~3+', 'cn*, o^n*', '1*>, io2>', '1X.n<>', '1-4+', 'n=, 1+', '1X, 1>', 'n+.nX, nX.n+', '1<>.nX', 'n+, nX<, 1X>, ~2X>', '1>, io2>',
          'o1>, c1*>, io2>', 'o1>=, c1X>', '1+, ~2/3', 'on*, c^*', '~1/2, 1-2X, ~2+', '1+ or2>, 2=, 1X> or1*', '1*, ~2*', '~0/2, ~1/2, ~2/2', '~2/4', 'o1+,c1X', '1*, ~1/3', 'on>, cnX>', '~2+, ~1/2', '1+, ~1/2, ~1/3', 'n(3+)', '~2/3.nX', '~2+, ~3+', '~1-2*<>', 'o1>, c1X>,~ 0/3,~ 3/3', '1X.n<>', 'n(1/2)', '~1/2, ~1/3', '~1/2.nX', 'nX', 'cnX, o^nX', 'n<>, 1+', '1=, 2X>', '1<>.nX>', '2+, 2X, ~1/2, ~1/3', '1+, ~2X', '1*, 2*', 'n+, n(~1/2)', '~1-2+ = 1+, ~2+', '1*, ~2+', 'n<>, nX<', 'n<>, nX>',
          '~1/2, ~1/3', '1*, ~1/3, ~2/3', '1X, ~1/3', '~1-2+ = 1+, ~2+', '~3X ~2/4 ~1/5', '3=, 1X>, 1+<', 'o1>, c1X>, final o2>', '~2/3', '~2/3', 'n(2/3)', '~1/3, ~1/4', '~0/0']
```