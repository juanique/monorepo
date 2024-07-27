package components

import (
	"github.com/juanique/monorepo/taco/core"
	"github.com/veandco/go-sdl2/sdl"
)

type Rect struct {
	H     int32
	W     int32
	Color core.Color

	pos *Position
}

type RectOpts struct {
	H     int32
	W     int32
	Color core.Color
}

func NewRect(pos *Position, opts RectOpts) *Rect {
	if opts.H == 0 {
		opts.H = 10
	}

	if opts.W == 0 {
		opts.W = 10
	}

	if opts.Color == core.NilColor {
		opts.Color = core.Black
	}

	return &Rect{
		H:     opts.H,
		W:     opts.W,
		Color: opts.Color,
		pos:   pos,
	}
}

func (c *Rect) Update() error {
	return nil
}

func (c *Rect) Draw(renderer *sdl.Renderer) error {
	rect := sdl.Rect{X: c.pos.Vect.X, Y: c.pos.Vect.Y, W: c.W, H: c.H}
	renderer.SetDrawColor(c.Color.R, c.Color.G, c.Color.B, c.Color.Alpha)
	renderer.DrawRect(&rect)

	return nil
}
