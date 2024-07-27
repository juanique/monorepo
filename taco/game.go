package taco

import (
	"github.com/juanique/monorepo/taco/components"
	"github.com/juanique/monorepo/taco/core"
	"github.com/veandco/go-sdl2/sdl"
)

type Game struct{}

type Player struct {
	// Not owned
	input *components.Input

	// Owned
	pos    *components.Position
	entity *components.Rect
}

type PlayerOpts struct {
	Pos core.Vector2
}

func NewPlayer(input *components.Input, opts PlayerOpts) *Player {
	pos := components.NewPosition(opts.Pos)
	entity := components.NewRect(pos, components.RectOpts{})

	return &Player{
		input:  input,
		pos:    pos,
		entity: entity,
	}
}

func (p *Player) Update() error {
	movement := core.Vector2{}
	if p.input.KeyPressed(sdl.SCANCODE_LEFT) {
		movement.X -= 1
	}
	if p.input.KeyPressed(sdl.SCANCODE_RIGHT) {
		movement.X += 1
	}
	if p.input.KeyPressed(sdl.SCANCODE_UP) {
		movement.Y -= 1
	}
	if p.input.KeyPressed(sdl.SCANCODE_DOWN) {
		movement.Y += 1
	}

	p.pos.Move(movement)
	return nil
}

func (p *Player) Draw(renderer *sdl.Renderer) error {
	return p.entity.Draw(renderer)
}

func (g *Game) Run(renderer *sdl.Renderer, scene core.Scene) {
	engine := NewEngine(renderer, scene)

	input := components.NewInput()
	fpsCounter := components.NewFPSCounter()
	player := NewPlayer(input, PlayerOpts{Pos: core.Vector2{X: scene.W / 2, Y: scene.H / 2}})

	engine.AddComponent(input)
	engine.AddComponent(fpsCounter)
	engine.AddComponent(player)

	engine.Run()
}
