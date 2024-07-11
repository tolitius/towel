> [!NOTE]
> _this area is ~~51~~ **42**_

# TODO

### plan serialization

* passing plan as a stream (of bytes)
* deserializing plan from a stream (of bytes)
* dealing with custom functions

### store and restore from plan checkpoints

* store runtime plan state to disk
* restore plan state from disk to continue execution

### error handling

* instructor / pydantic failures
* connection errors

### pluggable logging

* colorized printing/logging
* plug in a logger (file, kafka, sysout, etc.)

### making plan function

* given a plan and a problem, create all the functions to enable plan execution
