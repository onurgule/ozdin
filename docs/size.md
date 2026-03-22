# APK / uygulama boyutu

- Gereksiz font ve büyük görseller eklemeyin; sistem fontları tercih edin.
- Android: `--split-per-abi`, `minifyEnabled` / `shrinkResources` (release).
- `flutter build apk --split-per-abi` ile ABI başına daha küçük paketler.
- Bağımlılıkları minimumda tutun; ağır animasyon paketlerinden kaçının.
