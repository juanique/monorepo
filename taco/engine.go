package taco

import (
	"time"

	"github.com/juanique/monorepo/taco/components"
	"github.com/juanique/monorepo/taco/core"
	"github.com/veandco/go-sdl2/sdl"
)

const screenTicksPerFrame = time.Microsecond * 6944

type Engine struct {
	renderer   *sdl.Renderer
	scene      core.Scene
	components []components.Component
	Stopped    bool

	// Cap to ~144fps
	capTimer core.Timer
}

func NewEngine(renderer *sdl.Renderer, scene core.Scene) Engine {
	return Engine{
		renderer: renderer,
		scene:    scene,
	}
}

func (eng *Engine) AddComponent(component components.Component) {
	eng.components = append(eng.components, component)
}

func (eng *Engine) Update() {
	eng.capTimer.Start()
	for event := sdl.PollEvent(); event != nil; event = sdl.PollEvent() {
		switch event.(type) {
		case *sdl.QuitEvent:
			eng.Stopped = true
			return
		}
	}

	eng.renderer.SetDrawColor(255, 200, 200, 255)
	eng.renderer.Clear()

	for _, component := range eng.components {
		component.Update()
	}
	for _, component := range eng.components {
		component.Draw(eng.renderer)
	}

	eng.renderer.Present()

	frameTicks := eng.capTimer.GetTicks()
	if frameTicks < screenTicksPerFrame {
		delay := screenTicksPerFrame - frameTicks
		sdl.Delay(uint32(delay.Milliseconds()))
	}
}

func (eng *Engine) Run() {
	for {
		eng.Update()
		if eng.Stopped {
			return
		}
	}
}
