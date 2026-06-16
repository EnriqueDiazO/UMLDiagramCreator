#pragma once

enum class SoundKind {
    Tone
};

class Sound {
public:
    double duration() const;
    const char *name() const;
};
