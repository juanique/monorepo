package main

import (
	"fmt"
	"time"

	"github.com/juanique/monorepo/taco"
	"github.com/juanique/monorepo/taco/core"
	"github.com/veandco/go-sdl2/sdl"
	"github.com/veandco/go-sdl2/ttf"
)

const (
	screenWidth         = 600
	screenHeight        = 800
	screenTicksPerFrame = time.Microsecond * 6944
)

func main() {
	scene := core.Scene{H: screenHeight, W: screenWidth}
	if err := sdl.Init(sdl.INIT_EVERYTHING); err != nil {
		fmt.Println("initializing SDL:", err)
		return
	}

	if err := ttf.Init(); err != nil {
		fmt.Println("initializing SDL_FONT:", err)
		return
	}

	window, err := sdl.CreateWindow(
		"Gaming in Go Episode 2",
		sdl.WINDOWPOS_UNDEFINED, sdl.WINDOWPOS_UNDEFINED,
		screenWidth, screenHeight,
		sdl.WINDOW_OPENGL)
	if err != nil {
		fmt.Println("initializing window:", err)
		return
	}
	defer window.Destroy()

	renderer, err := sdl.CreateRenderer(window, -1, sdl.RENDERER_ACCELERATED)
	if err != nil {
		fmt.Println("initializing renderer:", err)
		return
	}
	defer renderer.Destroy()

	game := taco.Game{}
	game.Run(renderer, scene)
}
