"use client";

import { Chessboard } from "react-chessboard";
import type { PieceDropHandlerArgs, SquareHandlerArgs } from "react-chessboard";

interface BoardProps {
  fen?: string;
  orientation?: "white" | "black";
  onSquareClick?: (args: SquareHandlerArgs) => void;
  onPieceDrop?: (args: PieceDropHandlerArgs) => boolean;
  highlightSquares?: string[];
  interactive?: boolean;
}

export default function Board({
  fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  orientation = "white",
  onSquareClick,
  onPieceDrop,
  highlightSquares = [],
  interactive = true,
}: BoardProps) {
  const squareStyles: Record<string, React.CSSProperties> = {};
  for (const sq of highlightSquares) {
    squareStyles[sq] = { backgroundColor: "rgba(255, 255, 0, 0.4)" };
  }

  return (
    <Chessboard
      options={{
        position: fen,
        boardOrientation: orientation,
        onSquareClick: interactive ? onSquareClick : undefined,
        onPieceDrop: interactive ? onPieceDrop : undefined,
        squareStyles,
        allowDragging: interactive,
      }}
    />
  );
}
