#include <pybind11/pybind11.h>
#include "Sound.h"

namespace py = pybind11;

PYBIND11_MODULE(native_fixture, m) {
    py::class_<Sound>(m, "Sound")
        .def(py::init<>())
        .def("duration", &Sound::duration)
        .def_property_readonly("name", &Sound::name);

    py::enum_<SoundKind>(m, "SoundKind")
        .value("Tone", SoundKind::Tone);

    PRAAT_CLASS_BINDING(PraatSound, "PraatSound");
}
