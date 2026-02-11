# MSG Examples

Welcome to the **Mechanics of Structure Genome (MSG) Examples** repository! This collection demonstrates the use of VABS and SwiftComp for structural analysis of composite materials and structures.

[Examples](./examples/index.md)

## Getting Started

1. **Download the repository**: `git clone https://github.com/wenbinyugroup/msg-examples.git`
2. **Install dependencies**: `uv sync`
3. **Browse examples**: Each example folder contains at least:
   - `README.md` - Comprehensive documentation
   - `run.py` - Analysis scripts
   - `visualization.ipynb` - Interactive results
4. **Run an example**:
   ```bash
   cd examples/gmsh_t18
   python run.py
   jupyter notebook visualization.ipynb
   ```

## Resources

### Documentation

- [SGIO](https://wenbinyugroup.github.io/sgio/): Python interface for structure genome I/O

### Community

You're welcome to post any questions or comments on the [cdmHUB community](https://community.cdmhub.org/).

### Contribution

1. Clone or fork the repository
2. Create a new branch for your example: `git checkout -b my_example`
3. Copy the template: `cp -r examples/_template/ examples/my_example/`
4. Implement your example in `my_example/`
5. Test and build: `myst build --html`
6. Submit a pull request

More details in [Contribution Guidelines](./doc/EXAMPLE_GUIDELINES.md).

---

**License**: See repository for license information  
**Maintainer**: Wenbin Yu Research Group


