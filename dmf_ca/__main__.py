import json
from .core import Context, Engine, Fact


def main():
    facts = tuple(Fact(k, v, "synthetic-fixture", 0, 1000, 90) for k, v in
                  (("role", "registrar"), ("purpose", "registration"), ("phase", "open")))
    engine = Engine()
    print(json.dumps({"open": engine.project(Context("registrar-1", 100, 100, facts)).to_dict(),
                      "expired": engine.project(Context("registrar-1", 1000, 1000, facts)).to_dict()}, indent=2))


if __name__ == "__main__":
    main()
