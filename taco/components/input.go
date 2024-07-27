package components

import (
	"github.com/veandco/go-sdl2/sdl"
)

type Input struct {
	keyboardState []uint8
}

func NewInput() *Input {
	return &Input{}
}

func (c Input) KeyPressed(keyCode uint8) bool {
	return c.keyboardState[keyCode] == 1
}

func (c *Input) Update() error {
	c.keyboardState = sdl.GetKeyboardState()
	return nil
}

func (c *Input) Draw(renderer *sdl.Renderer) error {
	return nil
}
