package core

import (
	"math"
	"time"

	"github.com/veandco/go-sdl2/sdl"
)

type Timer struct {
	StartTicks  uint64
	PausedTicks uint64
	Paused      bool
	Started     bool
}

func (t *Timer) Start() {
	t.Started = true
	t.Paused = false
	t.StartTicks = sdl.GetTicks64()
}

func (t *Timer) Stop() {
	t.Started = false
	t.Paused = false
	t.StartTicks = 0
	t.PausedTicks = 0
}

func (t *Timer) Reset() {
	t.Stop()
	t.Start()
}

func (t *Timer) Pause() {
	t.Paused = true
	t.PausedTicks = sdl.GetTicks64() - t.StartTicks
	t.StartTicks = 0
}

func (t *Timer) Unpause() {
	if !t.Started || !t.Paused {
		return
	}

	t.Paused = false
	t.StartTicks = sdl.GetTicks64() - t.PausedTicks
	t.PausedTicks = 0
}

func (t *Timer) GetTicks() time.Duration {
	if !t.Started {
		return 0
	}

	if t.Paused {
		if t.PausedTicks > math.MaxInt64 {
			panic("Could not cast to int64")
		}
		return time.Millisecond * time.Duration(int64(t.PausedTicks))
	}

	ticks := sdl.GetTicks64() - t.StartTicks
	if ticks > math.MaxInt64 {
		panic("Could not cast to int64")
	}
	return time.Millisecond * time.Duration(int64(ticks))
}
