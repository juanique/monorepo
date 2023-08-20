package main

import "fmt"
import "os"
import "log"
import "github.com/bazelbuild/rules_go/go/runfiles"
import "os/exec"


func main() {
	ruffBin, err := runfiles.Rlocation("ruff/ruff")

	if err != nil {
		panic(err)
	}

	fmt.Printf("Hello %v\n", os.Args)
	fmt.Printf("ruff is in %v\n", ruffBin)

	out, err := exec.Command(ruffBin, os.Args[1:]...).Output()
    if err != nil {
		fmt.Printf("Ruff error code is %v\n", err)
		fmt.Println("Ruff error message: ", string(out))
        log.Fatal(err)
    }
    fmt.Printf("The date is %s\n", out)
}