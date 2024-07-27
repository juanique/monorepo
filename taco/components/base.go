package components

import "github.com/veandco/go-sdl2/sdl"

type Component interface {
	Update() error
	Draw(renderer *sdl.Renderer) error
}
