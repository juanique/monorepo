package main

import (
	"fmt"
	"go/importer"

	"github.com/veandco/go-sdl2/sdl"
)

func main() {
	fmt.Println("hello world")
	// Create a new importer
	importer := importer.For("source", nil)

	// Import the package
	pkg, err := importer.Import("sdl")
	if err != nil {
		fmt.println("error:", err)
		return
	}

	sdl.Scope()
	// Iterate over the scope's names
	scope := pkg.Scope()
	for _, name := range scope.Names() {
		obj := scope.Lookup(name)
		if obj.Exported() {
			fmt.Println(name, obj.Type())
		}
	}
}
