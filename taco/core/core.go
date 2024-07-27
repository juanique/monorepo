package core

import "fmt"

type Scene struct {
	H int32
	W int32
}

type Color struct {
	R     uint8
	G     uint8
	B     uint8
	Alpha uint8
}

var NilColor = Color{0, 0, 0, 0}
var Black = Color{0, 0, 0, 255}

type Vector2 struct {
	X int32
	Y int32
}

func (v *Vector2) Add(other Vector2) {
	v.X += other.X
	v.Y += other.Y
}

func (v Vector2) String() string {
	return fmt.Sprintf("Vector2{%d, %d}", v.X, v.Y)
}
