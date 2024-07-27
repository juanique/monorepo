package components

import (
	"github.com/juanique/monorepo/taco/core"
	"github.com/veandco/go-sdl2/sdl"
)

type Position struct {
	Vect core.Vector2
}

func NewPosition(vect core.Vector2) *Position {
	return &Position{
		Vect: vect,
	}
}

func (c *Position) Move(vector core.Vector2) {
	c.Vect.Add(vector)
}

func (c *Position) Update() error {
	return nil
}

func (c *Position) Draw(renderer *sdl.Renderer) error {
	return nil
}
