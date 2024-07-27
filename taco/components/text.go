package components

import (
	"github.com/juanique/monorepo/taco/core"
	"github.com/veandco/go-sdl2/sdl"
	"github.com/veandco/go-sdl2/ttf"
)

type Text struct {
	Msg   string
	Size  int
	Color core.Color

	// Owned
	font *ttf.Font

	// Not owned
	pos *Position
}

type TextOpts struct {
	Msg          string
	FontFilename string
	Color        core.Color
	Size         int
}

func NewText(pos *Position, opts TextOpts) *Text {
	if opts.FontFilename == "" {
		opts.FontFilename = "default_text.ttf"
	}

	if opts.Color == core.NilColor {
		opts.Color = core.Black
	}

	if opts.Size == 0 {
		opts.Size = 12
	}

	font, err := ttf.OpenFont(opts.FontFilename, opts.Size)
	if err != nil {
		panic("Could not load font: " + err.Error())
	}

	return &Text{
		Msg:   opts.Msg,
		Size:  opts.Size,
		Color: opts.Color,
		font:  font,
		pos:   pos,
	}
}

func (c *Text) Update() error {
	return nil
}

func (c *Text) Draw(renderer *sdl.Renderer) error {
	surface, err := c.font.RenderUTF8Solid(
		c.Msg,
		sdl.Color{R: c.Color.R, G: c.Color.G, B: c.Color.B, A: c.Color.Alpha},
	)
	if err != nil {
		panic("Could not render font.")
	}
	defer surface.Free()

	texture, err := renderer.CreateTextureFromSurface(surface)
	if err != nil {
		panic("Could not create texture for text.")
	}
	defer texture.Destroy()

	position := sdl.Rect{X: c.pos.Vect.X, Y: c.pos.Vect.Y, W: surface.W, H: surface.H}
	renderer.Copy(texture, nil, &position)

	return nil
}

func (c *Text) Destroy() {
	c.font.Close()
}
