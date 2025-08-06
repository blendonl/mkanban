# Maintainer: Your Name <your.email@example.com>
pkgname=mkanban
pkgver=1.0.0
pkgrel=1
pkgdesc="A Terminal User Interface Kanban Board"
arch=('any')
url="https://github.com/yourusername/mkanban"
license=('MIT')
depends=('python' 'python-textual' 'python-pydantic' 'python-frontmatter' 'python-click')
makedepends=('python-setuptools')
source=("$pkgname-$pkgver.tar.gz::$url/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
    cd "$pkgname-$pkgver"
    python setup.py build
}

package() {
    cd "$pkgname-$pkgver"
    python setup.py install --root="$pkgdir/" --optimize=1 --skip-build
}