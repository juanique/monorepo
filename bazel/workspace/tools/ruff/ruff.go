package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"

	"github.com/bazelbuild/rules_go/go/runfiles"
)

func main() {
	ruffBin, err := runfiles.Rlocation("ruff/ruff")
	if err != nil {
		panic(err)
	}

	out, err := exec.Command(ruffBin, os.Args[1:]...).Output()
	if err != nil {
		fmt.Println("Ruff error message: ", string(out))
		log.Fatal(err)
	}
}
