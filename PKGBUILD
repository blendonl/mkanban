pkgname=mkanban
pkgver=0.2.6
pkgrel=1
pkgdesc="A Terminal User Interface Kanban Board"
arch=('any')
url="https://github.com/blendonl/mkanban"
license=('MIT')
depends=('python' 'python-textual' 'python-pydantic' 'python-frontmatter' 'python-click' 'python-linkify-it-py' 'python-aiohttp' 'python-dotenv')
makedepends=('python-build' 'python-installer' 'python-wheel')
source=("$pkgname-$pkgver::file://${PWD}")
sha256sums=('SKIP')

build() {
    cd "$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$pkgname-$pkgver"
    python -m installer --destdir="$pkgdir" dist/*.whl
}
