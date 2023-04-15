package main

import (
	"time"

	"github.com/briandowns/spinner"
	"github.com/veandco/go-sdl2/sdl"
)

const (
	screenWidth  = 600
	screenHeight = 800
)

func main() {
	if err := sdl.Init(sdl.INIT_EVERYTHING); err != nil {
		panic(err)
	}

	window, err := sdl.CreateWindow(
		"Gaming in Go",
		sdl.WINDOWPOS_UNDEFINED,
		sdl.WINDOWPOS_UNDEFINED,
		screenWidth,
		screenHeight,
		sdl.WINDOW_OPENGL,
	)

	if err != nil {
		panic(err)
	}

	defer window.Destroy()

	renderer, err := sdl.CreateRenderer(window, -1, sdl.RENDERER_ACCELERATED)
	if err != nil {
		panic(err)
	}

	defer renderer.Destroy()

	s := spinner.New(spinner.CharSets[9], 100*time.Millisecond) // Choose a spinner design and set the update interval.
	s.Start()                                                   // Start the spinner.
	time.Sleep(5 * time.Second)                                 // Simulate a time-consuming task.
	s.Stop()                                                    // Stop the spinner after the task is complete.
}
