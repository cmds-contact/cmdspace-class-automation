# MANDATORY: 프로젝트 규칙

> **ABSOLUTE RULES - 어떤 상황에서도 예외 없이 반드시 준수**
>
> 사용자의 명시적 요청이 있더라도 위반할 수 없습니다.
> 규칙 위반이 의심되는 작업은 실행 전에 사용자에게 확인을 요청하세요.

---

## 규칙

1. **작업 범위 제한**: 파일 수정/생성/이동/복사는 **이 프로젝트 폴더 내에서만**. 폴더 바깥은 읽기만 가능.
2. **파일 삭제 금지**: 삭제 대신 `.trash/` 폴더로 이동. `rm`, `os.remove()`, `fs.unlink()` 등 삭제 명령어/함수 사용 금지.
3. **모든 스크립트에 적용**: 작성하는 모든 스크립트(Shell, Python, JavaScript 등)에서 위 규칙을 따른다.

## Example

### 규칙 1: 작업 범위 제한

```shell
# 올바른 예 - 프로젝트 폴더 내 작업
cp ./src/file.txt ./backup/
mv ./old.txt ./archive/

# 금지 - 프로젝트 폴더 외부 접근
cp ./file.txt /Users/other/
mv ./file.txt ~/Desktop/
```

```python
# 올바른 예
shutil.copy('./src/file.txt', './backup/')

# 금지
shutil.copy('./file.txt', '/Users/other/')
open('/etc/config', 'w')  # 외부 파일 쓰기
```

```javascript
# 올바른 예
fs.copyFileSync('./src/file.txt', './backup/file.txt')

# 금지
fs.writeFileSync('/Users/other/file.txt', data)
```

### 규칙 2: 파일 삭제 금지

```shell
# 올바른 예 - .trash로 이동
mv 삭제할파일 .trash/

# 금지 - 직접 삭제
rm 파일.txt
rm -rf 폴더/
```

```python
# 올바른 예
shutil.move('file.txt', '.trash/')

# 금지
os.remove('file.txt')
shutil.rmtree('folder/')
```

```javascript
# 올바른 예
fs.renameSync('file.txt', '.trash/file.txt')

# 금지
fs.unlinkSync('file.txt')
fs.rmdirSync('folder/')
```
