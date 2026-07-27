// 飞书视频文件 Token 提取脚本
// 在飞书文件夹页面 (https://*.feishu.cn/drive/folder/...) 打开控制台粘贴运行

(function(){
  var s = window.store || window.__store__;
  if(!s) {
    console.error('❌ 未找到页面 store，请确认在飞书文件夹页面');
    return;
  }
  
  var st = s.getState ? s.getState() : s.state;
  var obs = st.entities && st.entities.objs;
  if(!obs) {
    console.error('❌ 未找到文件列表数据');
    return;
  }
  
  var result = [];
  Object.keys(obs).forEach(function(k){
    var obj = obs[k];
    var data = obj.toJS ? obj.toJS() : obj;
    if(data.name && data.name.endsWith('.mp4')){
      result.push({
        name: data.name,
        token: data.obj_token || k
      });
    }
  });
  
  result.sort(function(a, b){
    return a.name.localeCompare(b.name, undefined, {numeric: true});
  });
  
  console.log('✅ 找到 ' + result.length + ' 个视频文件:\n');
  console.log(JSON.stringify(result, null, 2));
  
  // 同时保存到全局变量
  window._feishuFiles = result;
  console.log('\n💡 数据已保存到 window._feishuFiles');
  console.log('   复制上面的 JSON 保存为 files.json 即可使用 download.py');
})();
