import { useState } from "react";

function calculateWinner(squares: string[]): string | null {
    const lines = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [2, 4, 6],
    ];
    for (const line of lines) {
        const [a, b, c] = line;
        if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
            return squares[a];
        }
    }
    return null;
}

// Value defaults to empty string
function Square({ value = "", onSquareClick }: { value: string, onSquareClick: () => void }) {
    function handleClick() {
        onSquareClick();
    }
    return <button className="square" onClick={handleClick}>{value}</button>
}

export default function Board() {
    const [squares, setSquares] = useState(Array(9).fill(""));
    const [isXNext, setIsXNext] = useState(true);

    function onSquareClick(index: number) {
        if (squares[index] !== "") {
            return;
        }

        var newState = squares.slice();
        newState[index] = isXNext ? "X" : "O";
        setSquares(newState);
        setIsXNext(!isXNext);

        console.log("Next player: " + (isXNext ? "X" : "O"));

    }

    const winner = calculateWinner(squares);
    let status = "";
    if (winner) {
        status = `Winner: ${winner}`;
    } else {
        status = "Next player: " + (isXNext ? "X" : "O");
    }

    return <>
        <div className="status">{status}</div>
        <div className="board">
            <Square value={squares[0]} onSquareClick={() => onSquareClick(0)} />
            <Square value={squares[1]} onSquareClick={() => onSquareClick(1)} />
            <Square value={squares[2]} onSquareClick={() => onSquareClick(2)} />
            <Square value={squares[3]} onSquareClick={() => onSquareClick(3)} />
            <Square value={squares[4]} onSquareClick={() => onSquareClick(4)} />
            <Square value={squares[5]} onSquareClick={() => onSquareClick(5)} />
            <Square value={squares[6]} onSquareClick={() => onSquareClick(6)} />
            <Square value={squares[7]} onSquareClick={() => onSquareClick(7)} />
            <Square value={squares[8]} onSquareClick={() => onSquareClick(8)} />
        </div>
    </>
}
