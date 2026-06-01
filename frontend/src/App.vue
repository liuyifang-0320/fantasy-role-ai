<script>
export default {
  onLaunch() {
    console.log('Fantasy Role AI launched')
  },
}
</script>

<style lang="scss">
@import './uni.scss';

page {
  min-height: 100%;
  color: #f8f7ff;
  background: #130c2f;
  font-family: 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
}

view,
text,
button,
input,
textarea {
  box-sizing: border-box;
}

button::after {
  border: none;
}
</style>
