package main

import (
	"time"

	"github.com/briandowns/spinner"
)

func main() {
	s := spinner.New(spinner.CharSets[9], 100*time.Millisecond) // Choose a spinner design and set the update interval.
	s.Start()                                                   // Start the spinner.
	time.Sleep(5 * time.Second)                                 // Simulate a time-consuming task.
	s.Stop()                                                    // Stop the spinner after the task is complete.
}
