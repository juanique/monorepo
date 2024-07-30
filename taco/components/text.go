package components

import (
	"github.com/juanique/monorepo/taco/core"
	"github.com/veandco/go-sdl2/sdl"
	// "github.com/veandco/go-sdl2/ttf"
)

type Text struct {
	Msg   string
	Size  int
	Color core.Color

	// Owned
	// font *ttf.Font

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

	// font, err := ttf.OpenFont(opts.FontFilename, opts.Size)
	// if err != nil {
	// panic("Could not load font: " + err.Error())
	// }

	return &Text{
		Msg:   opts.Msg,
		Size:  opts.Size,
		Color: opts.Color,
		// font:  font,
		pos: pos,
	}
}

func (c *Text) Update() error {
	return nil
}

func (c *Text) Draw(renderer *sdl.Renderer) error {
	return nil
}

func (c *Text) Destroy() {
	// c.font.Close()
}
