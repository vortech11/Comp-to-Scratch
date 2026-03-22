# Quirks of the compiler

As of version 2.0.0, The quality of the syntax is durastically improved.

However, it could still be useful to take note of the syntax at times.

## Whitespace

All whitespace is allowed.

```ts
sprite cat{
        script         [
start    (  )     ;
      move () ;
  if   (1  == 1 )  { move
  (3)}
]
    }
```

It looks horrible, but it works

## Brackets

All types of brackets are interchangeable*

Brackets include:

- brackets: `[]`

- curly brackets: `{}`

- parenthesis: `()`

```ts
sprite cat(
    script{
        start(};
        move{3);
    ]
}
```

## Strings

There are no strings

What double quotes (`""`) do is include everything inside of it as one token.

This is useful for hex values

```ts
pen_setPenColorToColor("#ffffff");
```

This is also important for decimal values

```ts
move("10.3");
```

!!! warning "If you do not have double quotes with decimal or hex values, the compiler will throw an error"

## Semicolons

Semicolons are relatively normal except for the fact that they must come after every function and command, excluding curly brackets.

!!! failure "This does not work"
    ```ts
    if (5 == 3){
        move(10);
    };
    move(3);
    ```

!!! failure "This does not work"
    ```ts
    if (5 == 3)(
        move(10);
    )
    move(3);
    ```


Instead it should look something like this:

!!! success ""
    ```ts
    if (5 == 3){
        move(10);
    }
    move(3);
    ```

...or this

!!! success ""
    ```ts
    if (5 == 3)(
        move(10);
    );
    move(3);
    ```