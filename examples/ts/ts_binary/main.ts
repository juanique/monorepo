enum Greeting {
    Hello = "Hello",
    World = "World"
}

// Function with typed parameters and return type
function greet(name: string): string {
    return `${Greeting.Hello}, ${name}!`;
}

console.log(greet(Greeting.World));
