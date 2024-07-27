package components

import (
	"fmt"
	"time"

	"github.com/juanique/monorepo/taco/core"
	"github.com/veandco/go-sdl2/sdl"
)

type FPSCounter struct {
	frames int64
	timer  core.Timer
	fps    float64
	period time.Duration

	// Owned
	pos  *Position
	text *Text
}

func NewFPSCounter() *FPSCounter {
	return &FPSCounter{
		text: NewText(NewPosition(core.Vector2{}), TextOpts{}),
	}
}

func (fpsCounter *FPSCounter) Destroy() {
	fpsCounter.text.Destroy()
}

func (fpsCounter *FPSCounter) Update() error {
	if !fpsCounter.timer.Started {
		fpsCounter.timer.Start()
	}

	if fpsCounter.period == 0 {
		fpsCounter.period = time.Millisecond * 500
	}

	fpsCounter.frames += 1

	if fpsCounter.timer.GetTicks() > fpsCounter.period {
		fpsCounter.fps = float64(fpsCounter.frames) / fpsCounter.timer.GetTicks().Seconds()
		fpsCounter.timer.Reset()
		fpsCounter.frames = 0
	}

	return nil
}

func (fpsCounter *FPSCounter) Draw(renderer *sdl.Renderer) error {
	fpsCounter.text.Msg = fmt.Sprintf("%.0f FPS", fpsCounter.fps)
	fpsCounter.text.Draw(renderer)

	return nil
}
